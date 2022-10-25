"""
Design Choices:

"""
from min_heap import MinHeap, MinHeapNode
from typing import Any


class CacheSlot:
    """
    Represents each slot in the cache

    Data members:
        key: key of the data being cached
        value: value being cahced
        expire: time at which the cache will expire
        next: pointer to the next cache slot in the same cache line(same priority)
        prev: pointer to the previous cache slot in the same cache line (same priority)
        heap_index: index in the expiration min heap cache where the expiration time for the cahce slot is stored. 
                    This helps in reducing time complexity of delete funtion in heap to be restricted to O(logN) 
                    as search in heap is O(N) - (space vs time).

    """

    def __init__(self, key: str = "", val: Any = 0, priority: int = 0, expiration:int = 0):
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
    def initialize_slot(self, key: str="", val: Any = 0, priority: int = 0, expiration: int = 0) -> None:
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
    This class represents our cache and its associated function
    """
    def __init__(self, max_items: int):
        self.maxItems = max_items

        # number of filled CacheSlots
        self.cache_size = 0

        # Simulation of Cache slots
        # If empty cache is full
        self.free_list = [CacheSlot(key="FreeListHead") for i in range(max_items)]

        # Hash Map to map every key value in the array to slot in the cache
        # Achieves O(1) lookup time for our Get() [Trading space for speed]
        self.key_map = dict()

        # Keep track of available priority buckets in the cache
        # Achieves O(1) lookup        
        self.priority_buckets = dict()

        # Priority Queue to get the least priority bucket available in the cache in O(1)
        self.min_priority_heap = MinHeap()

        # Priority Queue to maintain the expiriation time of each cache slot
        # if the current time > expirationTime evict the slot during eviction
        # The implemetation is documented in the rescpective code file
        self.min_expire_heap = MinHeap()

    def remove_slot(self, slot: CacheSlot, priority: int) -> None:

        priority_bucket = self.priority_buckets[priority]

        # TODO: Need to do error handling here
        if not priority_bucket.cache_line_size:
            print("Error in remove slot")
            return

        # remove the slot from the list
        # connect the next and previous slots in list
        slot.prev.next = slot.next
        slot.next.prev = slot.prev
        slot.prev = slot.next = None

        priority_bucket.cache_line_size -= 1
        self.cache_size -= 1
        if not priority_bucket.cache_line_size:
            self.min_priority_heap.delete(priority_bucket.heap_index)
            del self.priority_buckets[priority_bucket.priority]


    def add_slot_to_head(self, slot: CacheSlot, priority: int) -> None:
        
        # O(1)
        
        if slot.priority not in self.priority_buckets:
            # create a new priority bucket
            self.priority_buckets[priority] = PriorityBucket(priority)
            # insert the priority to the heap
            self.min_priority_heap.add(MinHeapNode(priority, self.priority_buckets[priority]))

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

    def evict_slot_from_tail(self, priority: int) -> None:

        if priority not in self.priority_buckets:
            return
        # remove a slot from the tail of the given priority
        priority_bucket = self.priority_buckets[priority]
        # Check if the priority bucket contains any cache slots
        if not priority_bucket.cache_line_size:
            print("ERORR evict slot")
            return

        # get the least recently used cache slot
        slot_to_evict = priority_bucket.tail.prev

        self.remove_slot(slot_to_evict, priority)

        # remove the entry from the expiry heap
        # O(logn)
        self.min_expire_heap.delete(slot_to_evict.heap_index)
        
        # add the slot back to free lists
        # O(1)
        self.free_list.append(slot_to_evict)

        # remove the key from the key_map
        # O(1)
        del self.key_map[slot_to_evict.key]

    def Get(self, key: str, current_time: int) -> tuple:

        # if the key exists in the cache, return the value only if it is not expired
        if key in self.key_map:
            slot = self.key_map[key]
            # Only return the value if the expiration time >= currentTime 
            if slot.expire >= current_time:
                # move the slot to head of priority bucket
                self.remove_slot(slot, slot.priority)
                self.add_slot_to_head(slot, slot.priority)
                return True, self.key_map[key].value

        # if the key does not exist return None
        return False, None

    # Evict items to make room for new ones
    def Evict(self, current_time: int) -> None:
        # Check if there are any expired cache items
        # why while? there maybe some invalid equiry times in the heap as a result of update operation

        if self.min_expire_heap.peek() == -1:
            print("RAISE ERROR HERE AND EXIT")

        if self.min_expire_heap.peek().key < current_time:
            min_heap_node = self.min_expire_heap.pop()
            expired_cahe_slot = min_heap_node.node
            self.remove_slot(expired_cahe_slot, expired_cahe_slot.priority)
            
            self.free_list.append(expired_cahe_slot)
            # remove the key from the key_map
            del self.key_map[expired_cahe_slot.key]
            return


        # No slots have expired, so evict LRU cache slot from the lowest priority bucket
        least_priority_node = self.min_priority_heap.peek()
        if least_priority_node == -1:
            print("ERRORRRRR")
        
        self.evict_slot_from_tail(least_priority_node.key)


    def Set(self, key: str, value: Any, priority: int, expire: int, current_time: int) -> None:

        # if the key already exists in the cache
        if key in self.key_map:

            slot = self.key_map[key]

            previous_priority = slot.priority

            

            # initialize the slot again with new values
            slot.initialize_slot(key, value, priority, current_time + expire)
            
            # delete the previous expire time of the slot from the heap
            # O(logn) operation
            self.min_expire_heap.delete(slot.heap_index)

            # add the new expire time into the heap
            self.min_expire_heap.add(MinHeapNode(slot.expire, slot))


            # check if the priority for this key is still the same
            if previous_priority == priority:

                # just do a get to mark this as a recently accessed element and move it to the head of priority list
                self.Get(key, current_time)

            else:
                # remove the slot from the previous priority
                self.remove_slot(slot, previous_priority)

                # add the slot to the new priority bucket 
                self.add_slot_to_head(slot, priority)
            return

        # key does not exist in the cache
        if not self.free_list:
            self.Evict(current_time)

        cache_slot = self.free_list.pop()
        cache_slot.initialize_slot(key, value, priority, current_time + expire)

        # add the slot to the head of the priority bucket
        self.add_slot_to_head(cache_slot, priority)
        self.key_map[key] = cache_slot

        # add slot ot min expiry heap
        #O(logn)
        self.min_expire_heap.add(MinHeapNode(cache_slot.expire, cache_slot))

    def SetMaxItems(self, max_items: int, current_time: int):
        if self.cache_size > max_items:
            items_to_evict = self.cache_size - max_items
            while items_to_evict:
                self.Evict(current_time=current_time)
                items_to_evict -= 1
            self.free_list = []
        elif self.cache_size == max_items:
            self.free_list = []
        else:
            no_of_free_slots = max_items - self.cache_size

            self.free_list = self.free_list[:no_of_free_slots]
        
        self.maxItems = max_items

    def Keys(self):
        return list(self.key_map.keys())

c = PriorityExpiryCache(5)

c.Set(key="A", value=1, priority=5,  expire=100, current_time = 0)
c.Set(key="B", value=2, priority=15, expire=3, current_time=1)
print(c.Get("B", current_time=3))
c.Set(key="C", value = "blah", priority=5, expire= 40, current_time = 6)
print(c.Get(key = "A", current_time=7))
c.Set(key="D", value = 3, priority=20, expire = 50, current_time= 7)
print(c.Get(key="B", current_time=8))
c.Set(key="A", value=1, priority=20,  expire=100, current_time = 9)
c.Set(key="C", value = "blah", priority=20, expire= 40, current_time = 10)
c.Set(key="E", value = 'E', priority=20, expire= 40, current_time = 11)
print("No eviction till this point")
print(c.Get(key= "B", current_time=11))
print(c.Get(key= "A", current_time=11))
print(c.Get(key= "C", current_time=11))
print(c.Get(key= "D", current_time=11))
print(c.Get(key= "E", current_time=11))

print("Eviction Starts")
c.Set(key="G", value=2, priority=20, expire=70, current_time=13)
print(c.Get(key= "B", current_time=13))
c.Set(key="F", value=2, priority=1, expire=70, current_time=14)
print(c.Get(key= "G", current_time=15))
print(c.Get(key= "A", current_time=15))
print(c.Get(key= "C", current_time=15))
print(c.Get(key= "D", current_time=15))
print(c.Get(key= "E", current_time=15))