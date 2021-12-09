
import game.map.tiles as tiles
from game.actors.player import Player as PlayerActor
from game.callbacks import CallbackPack
from game.map.navigation import Coordinate, Direction
from game.map.rooms import Room, Area
from util.logger import Logger


class Map:
    WIDTH = 7
    HEIGHT = 3

    @staticmethod
    def __calculate_pos(pos_of_room: Coordinate, pos_in_room: Coordinate) -> Coordinate:
        """
        Calculates and returns a Coordinate on the Map corresponding to the Cooridante of a Room on the Map and
        a Coordinate in the Room.

        :param pos_of_room: Coordinate of the Room on the Map
        :param pos_in_room: Coordinate in the Room
        :return: Coordinate on the Map
        """
        x = pos_of_room.x * (Area.UNIT_WIDTH + 1) + pos_in_room.x
        y = pos_of_room.y * (Area.UNIT_HEIGHT + 1) + pos_in_room.y
        return Coordinate(x, y)

    def __init__(self, seed: int, rooms: "[[Room]]", player: PlayerActor, spawn_room: Coordinate, cbp: CallbackPack):
        self.__seed = seed
        self.__rooms = rooms
        self.__player = tiles.Player(player)
        self.__cbp = cbp

        self.__player_pos = Map.__calculate_pos(spawn_room, Coordinate(Area.MID_X, Area.MID_Y))
        self.__cur_area = self.__rooms[spawn_room.y][spawn_room.x]
        self.__cur_area.enter(Direction.Center)
        self.__cur_area.make_visible()

    @property
    def seed(self) -> int:
        return self.__seed

    @property
    def height(self) -> int:
        return Map.HEIGHT * (Area.UNIT_HEIGHT + 1) - 1

    @property
    def width(self) -> int:
        return Map.WIDTH * (Area.UNIT_WIDTH + 1) - 1

    @property
    def player_tile(self) -> tiles.Player:
        return self.__player

    @property
    def player_pos(self) -> Coordinate:
        return self.__player_pos

    def __get_area(self, x: int, y: int) -> (Area, tiles.Tile):
        """
        Calculates and returns the Room and in-room Coordinates of the given Map position.
        :param x: x position on the Map
        :param y: y position on the Map
        :return: Room or Hallway and their Tile at the given position
        """
        in_hallway = None
        width = Area.UNIT_WIDTH + 1
        height = Area.UNIT_HEIGHT + 1
        x_mod = x % width
        y_mod = y % height
        # position is in Hallway
        if x_mod == Area.UNIT_WIDTH:
            if y_mod == Area.UNIT_HEIGHT:
                # there are a few points on the map that are surrounded by Hallways and don't belong to any Room
                Logger.instance().error(f"Error! You should not be able to move outside of Hallways: {x}|{y}")
                return None, tiles.Invalid()
            x -= 1
            x_mod -= 1
            in_hallway = Direction.East
        elif y_mod == Area.UNIT_HEIGHT:
            y -= 1
            y_mod -= 1
            in_hallway = Direction.South

        room_x = int(x / width)
        room_y = int(y / height)
        room = self.__rooms[room_y][room_x]
        if room is None:
            Logger.instance().error(f"Error! Invalid position: {x}|{y}")
            return None, tiles.Invalid()

        if in_hallway:
            hallway = room.get_hallway(in_hallway)
            if hallway is None:
                return None, tiles.Invalid()
            if hallway.is_horizontal():
                return hallway, hallway.at(x_mod, 0)
            else:
                return hallway, hallway.at(0, y_mod)
        else:
            return room, room.at(x_mod, y_mod)

    def room_at(self, x: int, y: int) -> Room:
        if 0 <= x < Map.WIDTH and 0 <= y < Map.HEIGHT:
            return self.__rooms[y][x]
        return None

    def move(self, direction: Direction) -> bool:
        """
        Tries to move the player into the given Direction.
        :param direction: in which direction the player should move
        :return: True if the player was able to move, False otherwise
        """
        new_pos = self.__player_pos + direction
        if new_pos.y < 0 or self.height <= new_pos.y or \
                new_pos.x < 0 or self.width <= new_pos.x:
            return False

        area, tile = self.__get_area(new_pos.x, new_pos.y)
        if tile.is_walkable(direction, self.__player.player):
            if area != self.__cur_area:
                self.__cur_area.leave(direction)
                self.__cur_area = area
                self.__cur_area.enter(direction)

            if isinstance(tile, tiles.WalkTriggerTile):
                tile.on_walk(direction, self.player_tile.player)

            self.__player_pos = new_pos
            return True
        else:
            return False