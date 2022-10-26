"""
Design Choices: Please refer to the design_doc to understand how I landed at this design.

Unittest: Use the following command to run  the unittests - 
            $ python -m unittest -v tests.priority_expiry_cache_test    

"""

from min_heap import MinHeap, MinHeapNode
from typing import Any


class CacheSlot:
    """
    Represents each slot in the cache

    Data members:
        key: key of the data being cached
        value: value being cached
        expire: time at which the cache will expire
        next: pointer to the next cache slot in the same cache line(same priority)
        prev: pointer to the previous cache slot in the same cache line (same priority)
        heap_index: index in the expiration min heap cache where the expiration time for the cache slot is stored.
                    This helps in reducing time complexity of delete function in heap to be restricted to O(logN)
                    as search in heap is O(N) - (space vs time).

    """

    def __init__(self, key: str = "", val: Any = 0, priority: int = 0, expiration: int = 0):
        self.key = key
        self.value = val
        self.priority = priority
        self.expire = expiration
        self.next = None
        self.prev = None
        self.heap_index = -1

    """
    Intialize a cache slots with the given values. 
    This fucntion is called when the cache slot is popped from free list for assigning to a key.
    """

    def initialize_slot(self, key: str = "", val: Any = 0, priority: int = 0, expiration: int = 0) -> None:
        self.key = key
        self.value = val
        self.priority = priority
        self.expire = expiration
        self.heap_index = -1


class PriorityBucket:
    """
    This class represents individual Priority Buckets of given priority.
    This can be compared approximately to a cache line in set associative cache. 
    Data Members
        priority: priority this bucket represents
        head: head of the Doubly Lists pointing to the cache line within the priority
        tail: points to the last cahce slot within the bucket. 
        cache_line_size: number of chache items in this priority bucket.
        heap_index: helps in random access of the priority to be deleted from the min_heap.
                    This helps in reducing the time complexity of delete function in heap to O(logN)
    """

    def __init__(self, priority=0):
        self.priority = priority
        self.head = CacheSlot(key="PriorityHead")
        self.tail = CacheSlot(key="PriorityTail")
        self.head.next = self.tail
        self.tail.prev = self.head
        self.cache_line_size = 0
        self.heap_index = -1


class PriorityExpiryCache:
    """
    This class represents our cache and its associated functions.
    Data members: 
        maxItems: maximum number of items in the cache
        cache_size: number of filled cache slots.
        free_list: list of available cahce slots to fill. [Just for simulation of cache slots]
        key_map: HashMap to map a key and its corresponding cache slot. Provides O(1) lookup.
        priority_buckets: HashMap to map a priority and its corresponding priority bucket object.
        min_expire_heap: MinHeap for getting the minimum expiry time among all the cache slots.
        min_priority_heap: MinHeap for getting the minimum priority in the cache system.
    """

    def __init__(self, max_items: int):
        self.max_items = max_items

        # number of filled CacheSlots
        self.cache_size = 0

        # Simulation of Cache slots
        # If empty cache is full
        self.free_list = [CacheSlot(key="FreeListHead")
                          for i in range(max_items)]

        # Hash Map to map every key value in the array to slot in the cache
        # Achieves O(1) lookup time for our Get() [Trading space for speed]
        self.key_map = dict()

        # Keep track of available priority buckets in the cache
        # Achieves O(1) lookup
        self.priority_buckets = dict()

        # Priority Queue to get the least priority bucket available in the cache in O(1)
        self.min_priority_heap = MinHeap()

        # Priority Queue to maintain the expiration time of each cache slot
        # if the current time > expirationTime evict the slot during eviction
        # The implementation is documented in the respective code file
        self.min_expire_heap = MinHeap()

    def _remove_slot(self, slot: CacheSlot) -> None:
        """
        Removes the given cache slot from the priority bucket.  
        This is O(1) operation
        @param slot: cache slot to be deleted. 
        @return: None
        """

        try:
            priority = slot.priority

            # O(1) lookup. If the priority is empty, something went worng!
            # Program must error out!
            if priority not in self.priority_buckets:
                raise ValueError(
                    f"priority bucket: {priority} does not exist in the system. Trying to remove slot from a non "
                    f"existent priority bucket.")

            priority_bucket = self.priority_buckets[priority]

            if not priority_bucket.cache_line_size:
                raise Exception(f"Priority bucket {priority} is empty, cannot remove from an empty cache line")

            # remove the slot from the list
            # connect the next and previous slots in list
            slot.prev.next = slot.next
            slot.next.prev = slot.prev
            slot.prev = slot.next = None

            # decrement the cache size and number of items in the priority bucket.
            priority_bucket.cache_line_size -= 1
            self.cache_size -= 1

        # Handle exceptions - In our case exit without handling! In practical scenarios some error corrections?
        except ValueError:
            raise
        except BaseException:
            raise

    def _add_slot_to_head(self, slot: CacheSlot, priority: int) -> None:
        """
        Add the cache slot to the head of the priority bucket linked list.
        This is O(1) operation.

        @param slot: CacheSlot object to be add.
        @param priority: Priority bucket to which the cache slot must be added to. 
        @return: None
        """
        try:
            if slot.priority not in self.priority_buckets:
                # create a new priority bucket
                self.priority_buckets[priority] = PriorityBucket(priority)
                # insert the priority to the heap
                self.min_priority_heap.add(MinHeapNode(
                    priority, self.priority_buckets[priority]))

            priority_bucket = self.priority_buckets[slot.priority]

            # get the head of the cacheSlots in the priority bucket
            priority_bucket_head = priority_bucket.head

            # add slot to the list
            slot.next = priority_bucket_head.next
            slot.prev = priority_bucket_head

            # make the head and its current neighboring item to point to the slot
            priority_bucket_head.next.prev = slot
            priority_bucket_head.next = slot

            # increment the count of slots in this priority
            priority_bucket.cache_line_size += 1
            self.cache_size += 1
        except BaseException:
            raise

    def _evict_slot_from_tail(self, priority: int) -> None:
        """
        Removes tail cache slot (least recently used) from the given priority bucket. 
        This is O(logN) operation.

        @param slot: CacheSlot object to be add.
        @param priority: Priority bucket to which the cache slot must be added to. 
        @return: None
        """
        try:

            if priority not in self.priority_buckets:
                raise ValueError(
                    f"priority bucket: {priority} does not exist in the system. Trying to evict slot from a non existent priority bucket.")

                # remove a slot from the tail of the given priority
            priority_bucket = self.priority_buckets[priority]

            # Check if the priority bucket contains any cache slots
            if not priority_bucket.cache_line_size:
                raise Exception(
                    f"Priority bucket {priority} is empty, cannot remove a cache slot from an empty cahce line")

            # get the least recently used cache slot
            slot_to_evict = priority_bucket.tail.prev

            self._remove_slot(slot_to_evict)
            # if there are no more items belonging to the bucket - delete it! 
            if not priority_bucket.cache_line_size:
                # Time complexity of deleting from min priority heap is a O(logM).
                # where M is the number of priority buckets in the cache system. [upto 2^32]
                self.min_priority_heap.delete(priority_bucket.heap_index)
                del self.priority_buckets[priority_bucket.priority]

            # remove the entry from the expiry heap
            # O(logN)
            self.min_expire_heap.delete(slot_to_evict.heap_index)

            # add the slot back to free lists
            # O(1)
            self.free_list.append(slot_to_evict)

            # remove the key from the key_map
            # O(1)
            del self.key_map[slot_to_evict.key]

        except:
            raise

    def get(self, key: str, current_time: int) -> tuple:
        """
        Get the given key from cache. 
        If the key is present in the cache, move the slot to the head of the priority bucket doubly linked list.
        If key is not present, return False.
        This is an O(1) operation
        @param key: key to get from the slot.
        @param current_time: logical current time  
        @return: 
            If key found:(True, value)
            else: (False, None)
        """
        try:
            # if the key exists in the cache, return the value only if it is not expired
            # O(1)
            if key in self.key_map:
                slot = self.key_map[key]
                # Only return the value if the expiration time >= currentTime
                if slot.expire >= current_time:
                    # move the slot to head of priority bucket
                    # O(1)
                    self._remove_slot(slot)
                    self._add_slot_to_head(slot, slot.priority)
                    return True, self.key_map[key].value

            # if the key does not exist return None
            return False, None
        except:
            raise

    # Evict items to make room for new ones
    def _evict_item(self, current_time: int) -> None:
        """
        Evict an item from the cache.

        Eviction policy:
            - The function checks if there are any expired keys in the cache. If there is an expired
                item it evicts that slot from the cache.
            - If there are no expired items in the cache, then least priority bucket is chosen. 
            - If there are multiple slots in the bucket, slot from the tail of the priority bucket
              doubly linked list is removed.

        This is an O(LogN) operation

        @param current_time: logical current time  
        @return: None
        """
        try:

            if self.min_expire_heap.peek() == -1:
                raise Exception(
                    f"Oops something went wrong! No item in expiry min heap! This should not have happened.")

            # Check if any cache item is expired.
            if self.min_expire_heap.peek().key < current_time:
                # pop top the min expire heap node. This is the node that has expired.
                min_heap_node = self.min_expire_heap.pop()
                expired_cahe_slot = min_heap_node.node

                # Remove the slot from the priority bucket
                self._remove_slot(expired_cahe_slot)

                priority_bucket = self.priority_buckets[expired_cahe_slot.priority]

                # if there are no more items belonging to the bucket - delete it! 
                if not priority_bucket.cache_line_size:
                    # Time complexity of deleting from min priority heap is a O(logM).
                    # where M is the number of priority buckets in the cache system. [upto 2^32]
                    self.min_priority_heap.delete(priority_bucket.heap_index)
                    del self.priority_buckets[priority_bucket.priority]

                # add the slot back to the free list
                self.free_list.append(expired_cahe_slot)
                # remove the key from the key_map
                del self.key_map[expired_cahe_slot.key]
                return

            # No keys have expired, so evict LRU cache slot from the lowest priority bucket
            least_priority_node = self.min_priority_heap.peek()
            if least_priority_node == -1:
                raise Exception(
                    f"Oops something went wrong! No item in priority in min heap! This should not have happened.")

            self._evict_slot_from_tail(least_priority_node.key)
        except:
            raise

    def set(self, key: str, value: Any, priority: int, expire: int, current_time: int) -> None:
        """
        Add the given key to the cache along with setting its priority and expiry time.
        If the cache slot already exists in the cache update its values and move the cache 
        slot to head of the updated(or old) priority bucket.

        This is an O(logN) operation
        @param key: key to get from the slot.
        @param value: value for the corresponding key.
        @param priority: priority for the key.
        @param expire: time in seconds in that the key-value pair is valid for.
        @param current_time: logical current time  
        @return: None
        """
        try:
            # if the key already exists in the cache
            if key in self.key_map:

                slot = self.key_map[key]

                # remove the slot from the previous priority
                self._remove_slot(slot)

                priority_bucket = self.priority_buckets[slot.priority]

                # if there are no more items belonging to the bucket - delete it! 
                if not priority_bucket.cache_line_size:
                    # Time complexity of deleting from min priority heap is a O(logM).
                    # where M is the number of priority buckets in the cache system. [upto 2^32]
                    self.min_priority_heap.delete(priority_bucket.heap_index)
                    del self.priority_buckets[priority_bucket.priority]

                # initialize the slot again with new values
                slot.initialize_slot(key, value, priority, current_time + expire)

                # delete the previous expire time of the slot from the heap
                # O(logN) operation
                self.min_expire_heap.delete(slot.heap_index)

                # add the new expire time into the heap
                # O(logN)
                self.min_expire_heap.add(MinHeapNode(slot.expire, slot))

                # add the slot to the new priority bucket
                self._add_slot_to_head(slot, priority)

                return

            # key does not exist in the cache
            if not self.free_list:
                self._evict_item(current_time)

            if not self.free_list:
                raise Exception("something went wrong in eviction! Could not get the free slot.")

            cache_slot = self.free_list.pop()
            cache_slot.initialize_slot(key, value, priority, current_time + expire)

            # add the slot to the head of the priority bucket
            self._add_slot_to_head(cache_slot, priority)
            self.key_map[key] = cache_slot

            # add slot ot min expiry heap
            # O(logN)
            self.min_expire_heap.add(MinHeapNode(cache_slot.expire, cache_slot))

        except:
            raise

    def set_max_items(self, max_items: int, current_time: int) -> None:
        """
        Reset the capacity of the cache. 
        If the capacity is less than the current capacity, evict the required number of elements
        from the cache based on the eviction policy.
        @max_items: new capacity of the cache.
        @param current_time: logical current time  
        @return: None
        """
        try:
            if self.cache_size > max_items:
                items_to_evict = self.cache_size - max_items
                while items_to_evict:
                    self._evict_item(current_time=current_time)
                    items_to_evict -= 1
                self.free_list = list()
            elif self.cache_size == max_items:
                self.free_list = list()
            else:
                no_of_free_slots = max_items - self.cache_size

                self.free_list = self.free_list[:no_of_free_slots]

            self.max_items = max_items
        except:
            raise

    def keys(self):

        """
        Return the keys if the items stored in cache.
        """

        return list(self.key_map.keys())


c = PriorityExpiryCache(5)

c.set(key="A", value=1, priority=5, expire=100, current_time=0)
c.set(key="B", value=2, priority=15, expire=3, current_time=1)
print(c.get("B", current_time=3))
c.set(key="C", value="blah", priority=5, expire=40, current_time=6)
print(c.get(key="A", current_time=7))
c.set(key="D", value=3, priority=20, expire=50, current_time=7)
print(c.get(key="B", current_time=8))
c.set(key="A", value=1, priority=20, expire=100, current_time=9)
c.set(key="C", value="blah", priority=20, expire=40, current_time=10)
c.set(key="E", value='E', priority=20, expire=40, current_time=11)
print("No eviction till this point")
print(c.get(key="B", current_time=11))
print(c.get(key="A", current_time=11))
print(c.get(key="C", current_time=11))
print(c.get(key="D", current_time=11))
print(c.get(key="E", current_time=11))

print("Eviction Starts")
c.set(key="G", value=2, priority=20, expire=70, current_time=13)
print(c.get(key="B", current_time=13))
c.set(key="F", value=2, priority=1, expire=70, current_time=14)
print(c.get(key="G", current_time=15))
print(c.get(key="A", current_time=15))
print(c.get(key="C", current_time=15))
print(c.get(key="D", current_time=15))
print(c.get(key="E", current_time=15))

c = PriorityExpiryCache(5)
c.set("A", value=1, priority=5, expire=100, current_time=0)
c.set("B", value=2, priority=15, expire=3, current_time=0)
c.set("C", value=3, priority=5, expire=10, current_time=0)
c.set("D", value=4, priority=1, expire=15, current_time=0)
c.set("E", value=5, priority=5, expire=150, current_time=0)
print(c.get("C", current_time=0))
# Current time = 0
c.set_max_items(5, current_time=0)
print(c.keys())  # ["A", "B", "C", "D", "E"]
# space for 5 keys, all 5 items are included
# Current time = 5
c.set_max_items(4, current_time=5)
print(c.keys())  # ["A", "C", "D", "E"]
# // "B" is removed because it is expired.  expiry 3 < 5
c.set_max_items(3, current_time=5)
print(c.keys())  # ["A", "C", "E"]
# // "D" is removed because it the lowest priority
# // D's expire time is irrelevant.
c.set_max_items(2, current_time=5)
print(c.keys())  # ["C", "E"]
# // "A" is removed because it is least recently used."
# // A's expire time is irrelevant.
c.set_max_items(1, current_time=5)
print(c.keys())
# c.Keys() = ["C"]
