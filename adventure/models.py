from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
from uuid import uuid4

class Item(models.Model):
    name = models.CharField(max_length=50, default="DEFAULT ITEM")
    description = models.TextField(max_length=500, default="DEFAULT DESCRIPTION")

class Room(models.Model):
    title = models.CharField(max_length=50, default="DEFAULT TITLE")
    description = models.CharField(max_length=500, default="DEFAULT DESCRIPTION")
    n_to = models.IntegerField(default=0)
    s_to = models.IntegerField(default=0)
    e_to = models.IntegerField(default=0)
    w_to = models.IntegerField(default=0)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    def connectRooms(self, destinationRoom, direction):
        destinationRoomID = destinationRoom.id
        reverse_dirs = {"n": "s", "s": "n", "e": "w", "w": "e"}
        reverse_dir = reverse_dirs[direction]
        try:
            destinationRoom = Room.objects.get(id=destinationRoomID)
        except Room.DoesNotExist:
            print("That room does not exist")
        else:
            if direction == "n":
                self.n_to = destinationRoomID
            elif direction == "s":
                self.s_to = destinationRoomID
            elif direction == "e":
                self.e_to = destinationRoomID
            elif direction == "w":
                self.w_to = destinationRoomID
            else:
                print("Invalid direction")
                return
            setattr(destinationRoom, f"{reverse_dir}_to", self.id)
            destinationRoom.save()
            self.save()
    def playerNames(self, currentPlayerID):
        return [p.user.username for p in Player.objects.filter(currentRoom=self.id) if p.id != int(currentPlayerID)]
    def playerUUIDs(self, currentPlayerID):
        return [p.uuid for p in Player.objects.filter(currentRoom=self.id) if p.id != int(currentPlayerID)]
    def items_res(self):
        result = []
        for item in [i for i in RoomItem.objects.filter(room=self)]:
            result.append({
                'name': item.item.name,
                'description': item.item.description,
                'count': item.count,
            })
        return result


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    currentRoom = models.IntegerField(default=0)
    uuid = models.UUIDField(default=uuid4, unique=True)
    def initialize(self):
        if self.currentRoom == 0:
            self.currentRoom = Room.objects.first().id
            self.save()
    def room(self):
        try:
            return Room.objects.get(id=self.currentRoom)
        except Room.DoesNotExist:
            self.initialize()
            return self.room()
    def items_res(self):
        result = []
        for item in [i for i in Inventory.objects.filter(player=self)]:
            result.append({
                'name': item.item.name,
                'description': item.item.description,
                'count': item.count,
            })
        return result
    def get_item(self, name):
        room = Room.objects.get(id=self.currentRoom)
        item = room.items.get(name=name)
        # check the count of item
        room_item = RoomItem.objects.get(room=room, item=item)
        if room_item.count > 1:
            room_item.count -= 1
            room_item.save()
        elif room_item.count == 1:
            # remove from room
            room.items.remove(item)

        try:
            inventory = Inventory.objects.get(player=self, item=item)
            inventory.count += 1
            inventory.save()
        except Inventory.DoesNotExist:
            self.items.add(item)

        return f'You picked up the {item.name}'

    def drop_item(self, name):
        room = Room.objects.get(id=self.currentRoom)
        item = self.items.get(name=name)
        # check the count of item
        player_item = Inventory.objects.get(player=self, item=item)
        if player_item.count > 1:
            player_item.count -= 1
            player_item.save()
        elif player_item.count == 1:
            # remove from room
            self.items.remove(item)

        try:
            room_item = RoomItem.objects.get(room=room, item=item)
            room_item.count += 1
            room_item.save()
        except RoomItem.DoesNotExist:
            room.items.add(item)

        return f'You dropped the {item.name}'

@receiver(post_save, sender=User)
def create_user_player(sender, instance, created, **kwargs):
    if created:
        Player.objects.create(user=instance)
        Token.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_player(sender, instance, **kwargs):
    instance.player.save()

class Inventory(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    count = models.IntegerField(default=1)


class RoomItem(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, null=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, null=True)
    count = models.IntegerField(default=1)





