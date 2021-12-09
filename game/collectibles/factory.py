from game.collectibles.collectible import Collectible, ShopItem
from game.collectibles import consumable, pickup
from game.logic import instruction as gates
from util.my_random import RandomManager


class CollectibleFactory:
    def __init__(self, pool: "list of Collectibles") -> None:
        self.__pool = pool
        self.__rm = RandomManager.create_new()

    def produce(self) -> Collectible:
        return self.__rm.get_element(self.__pool)

    def produce_multiple(self, num_of_elements: int, unique_elements: bool = True) -> [Collectible]:
        if unique_elements:
            pool = self.__pool.copy()
            return [self.__rm.get_element(pool, remove=True) for i in range(num_of_elements)]
        else:
            return [self.__rm.get_element(self.__pool, remove=False) for i in range(num_of_elements)]


class GateFactory:
    @staticmethod
    def default():
        return CollectibleFactory(pool=[
            gates.HGate(), gates.XGate(), gates.YGate(), gates.ZGate(),
            gates.CXGate(), gates.SwapGate(),
        ])


class ShopFactory:
    @staticmethod
    def default() -> "ShopFactory":
        special_pool = [gates.HGate(), gates.XGate(), gates.HGate()]
        common_pool = [pickup.Key(1), pickup.Key(2), pickup.Heart(4), consumable.HealthPotion(2)]
        return ShopFactory(common_pool, special_pool, quality_level=1)

    def __init__(self, common_pool: [Collectible], special_pool: [Collectible], quality_level: int = 1,
                 min_items: int = 2, max_items: int = 5, discount: bool = False):
        """

        :param quality_level: how good the Shop should be, i.e. higher quality = better ShopItems
        :param pickup_pool: contains all Pickups the shop can sell
        :param special_pool: contains all Gates (and later other special Collectibles) that the Shop could offer
        :param min_items: minimum number of ShopItems available in the Shop
        :param max_items: maximum number of ShopItems available in the Shop
        :param discount: whether the ShopItems are 50% off or not
        """
        self.__common_pool = common_pool
        self.__special_pool = special_pool
        self.__quality_level = quality_level
        self.__min_items = min_items
        self.__max_items = max_items
        self.__discount = discount

        self.__rm = RandomManager.create_new()

    def produce(self, num_of_items: int = 0) -> [ShopItem]:
        """
        Produces a random list of ShopItems based on the factory's parameter. Said parameter are not changed allowing
        to produce multiple lists with the same factory. The only thing that obviously changes is the current seed of
        its random manager.

        :param num_of_items: if set to 0 or less, takes a random number of items in the factory's [min, max[ range
        :return: a list of randomly picked ShopItems based on the factory's parameter
        """
        shop_items = []
        special_items = self.__special_pool.copy()
        pickups = self.__common_pool.copy()
        if num_of_items <= 0:
            num_of_items = self.__rm.get_int(self.__min_items, self.__max_items)
        quality_level = self.__quality_level
        while len(shop_items) <= num_of_items:
            if quality_level > 0:
                # with a certain probability the next item will be a special one (1 is guaranteed at quality_level == 1)
                gets_special = self.__rm.get() < 1.0 / quality_level
            else:
                gets_special = False

            if gets_special and self.__special_pool is not None and len(special_items) > 0:
                item = self.__rm.get_element(special_items, remove=True)
            else:
                item = self.__rm.get_element(pickups, remove=False)

            # calculate the price with possibly a small variation
            if self.__discount:
                price = round(item.default_price() / 2)
            else:
                price_sigma = max(ShopItem.base_unit(), item.default_price() * 0.1)
                price = item.default_price() + round(self.__rm.get(-price_sigma, +price_sigma))

            shop_items.append(ShopItem(item, price))
            quality_level -= 1
        return shop_items