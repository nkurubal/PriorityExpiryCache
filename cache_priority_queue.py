# Get O(1)
# Set log(n)

# Check expiry
# Check priority
# Check LRU at given priority
from min_heap import MinHeap
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
        heap_index: index in the expiration min heap cache where the expiration time for the slot is stored
    """
    def __init__(self, key: str = "", val: Any = 0, priority: int = 0, expiration:int = 0):
        self.key = key
        self.value = val
        self.priority = priority
        self.expire = expiration
        self.next = None
        self.prev = None
        self.heap_index = -1

    def initialize_slot(self, key="", val=0, priority=0, expiration=0):
        self.key = key
        self.value = val
        self.priority = priority
        self.expire = expiration
        self.heap_index = -1


class PriorityBucket:
    """
    This class represents individual Priority Buckets. The class also holds 
    Data Members
        priority: priority this bucket represents
        head: head of the Doubly Lists pointing to the cache line within the priority
        tail: points to the last cahce slot within the bucket. 

    """

    def __init__(self, priority=0):
        self.priority = priority
        self.head = CacheSlot(key="PriorityHead")
        self.tail = CacheSlot(key="PriorityTail")
        self.head.next = self.tail
        self.tail.prev = self.head
        self.cacheLineSize = 0
        self.heap_index = -1




class PriorityExpiryCache:

    def __init__(self, max_items: int):
        self.maxItems = max_items

        # number of filled CacheSlots
        self.cacheSize = 0

        # Simulation of Cache slots
        # If empty cache is full
        self.freeList = [CacheSlot(key="FreeListHead") for i in range(max_items)]

        # Hash Map to map every key value in the array to slot in the cache
        # Achieves O(1) lookup time for our Get() [Trading space for speed]
        self.hashMap = dict()

        # Keep track of available priority buckets in the cache
        # Achieves O(1) lookup        
        self.priorityBuckets = dict()

        # Priority Queue to get the least priority bucket available in the cache in O(1)
        self.minPriorityHeap = MinHeap()

        # Priority Queue to maintain the expiriation time of each cache slot
        # if the current time > expirationTime evict the slot during eviction
        # The implemetation is documented in the rescpective code file
        self.minExpirationHeap = MinHeap()

    def remove_slot(self, slot: CacheSlot, priority: int) -> None:

        priority_bucket = self.priorityBuckets[priority]

        # TODO: Need to do error handling here
        if not priority_bucket.cacheLineSize:
            print("Error in remove slot")
            return

        # remove the slot from the list
        # connect the next and previous slots in list
        slot.prev.next = slot.next
        slot.next.prev = slot.prev
        slot.prev = slot.next = None

        priority_bucket.cacheLineSize -= 1
        self.cacheSize -= 1


    def add_slot_to_head(self, slot: CacheSlot, priority: int) -> None:
        
        # O(1)
        
        if slot.priority not in self.priorityBuckets:
            # create a new priority bucket
            self.priorityBuckets[priority] = PriorityBucket(priority)
            # insert the priority to the heap
            self.minPriorityHeap.add(MinHeapNode(priority, self.priorityBuckets[priority]))

        priority_bucket = self.priorityBuckets[slot.priority]

        # get the head of the cacheSlots in the priority bucket
        priority_bucket_head = priority_bucket.head

        # add slot to the list
        slot.next = priority_bucket_head.next
        slot.prev = priority_bucket_head

        # make the head and its current neighboring item to point to the slot
        priority_bucket_head.next.prev = slot
        priority_bucket_head.next = slot

        # increment the count of slots in this priority
        priority_bucket.cacheLineSize += 1
        self.cacheSize += 1

    def evict_slot_from_tail(self, priority: int) -> None:

        if priority not in self.priorityBuckets:
            return
        # remove a slot from the tail of the given priority
        priority_bucket = self.priorityBuckets[priority]
        # Check if the priority bucket contains any cache slots
        if not priority_bucket.cacheLineSize:
            print("ERORR evict slot")
            return

        # get the least recently used cache slot
        slot_to_evict = priority_bucket.tail.prev

        self.remove_slot(slot_to_evict, priority)

        # if the priority bucket becomes empty
        if not priority_bucket.cacheLineSize:
            # delete the bucket from the cache
            self.minPriorityHeap.delete(priority_bucket.heap_index)
            del self.priorityBuckets[priority_bucket.priority]
        # remove the entry from the expiry heap
        # O(logn)
        self.minExpirationHeap.delete(slot_to_evict.heap_index)
        
        # add the slot back to free lists
        # O(1)
        self.freeList.append(slot_to_evict)

        # remove the key from the hashMap
        # O(1)
        del self.hashMap[slot_to_evict.key]

    def Get(self, key: str, current_time: int) -> tuple:

        # if the key exists in the cache, return the value only if it is not expired
        if key in self.hashMap:
            slot = self.hashMap[key]
            # Only return the value if the expiration time >= currentTime 
            if slot.expire >= current_time:
                # move the slot to head of priority bucket
                self.remove_slot(slot, slot.priority)
                self.add_slot_to_head(slot, slot.priority)
                return True, self.hashMap[key].val

        # if the key does not exist return None
        return False, None

    # Evict items to make room for new ones
    def Evict(self, current_time: int) -> None:
        # Check if there are any expired cache items
        # why while? there maybe some invalid equiry times in the heap as a result of update operation

        if self.minExpirationHeap.peek() == -1:
            print("RAISE ERROR HERE AND EXIT")

        if self.minExpirationHeap.peek().key < current_time:
            min_heap_node = self.minExpirationHeap.pop()
            expired_cahe_slot = min_heap_node.node
            self.remove_slot(expired_cahe_slot, expired_cahe_slot.priority)
            priorityBucket = self.priorityBuckets[expired_cahe_slot.priority]
            if not priorityBucket.cacheLineSize:
                self.minPriorityHeap.delete(priorityBucket.heap_index)
                del self.priorityBuckets[priorityBucket.priority]
            
            self.freeList.append(expired_cahe_slot)
            # remove the key from the hashMap
            del self.hashMap[expired_cahe_slot.key]
            return


        # No slots have expired, so evict LRU cache slot from the lowest priority bucket
        least_priority_node = self.minPriorityHeap.peek()
        if least_priority_node == -1:
            print("ERRORRRRR")
        
        self.evict_slot_from_tail(least_priority_node.key)

        
        # if self.minPriorityHeap:
        #     min_priority = self.minPriorityHeap[0]
        #     self.evict_slot_from_tail(min_priority)
        # else:
        #     print("Evict error, this should not have happended")

    def Set(self, key: str, value: Any, priority: int, expire: int, current_time: int) -> None:

        # if the key already exists in the cache
        if key in self.hashMap:

            slot = self.hashMap[key]

            previous_priority = slot.priority

            

            # initialize the slot again with new values
            slot.initialize_slot(key, value, priority, current_time + expire)
            
            # delete the previous expire time of the slot from the heap
            # O(logn) operation
            self.minExpirationHeap.delete(slot.heap_index)

            # add the new expire time into the heap
            self.minExpirationHeap.add(MinHeapNode(slot.expire, slot))


            # check if the priority for this key is still the same
            if previous_priority == priority:

                # just do a get to mark this as a recently accessed element and move it to the head of priority list
                self.Get(key, current_time)

            else:
                # remove the slot from the previous priority
                self.remove_slot(slot, previous_priority)
                # if the priority bucket becomes empty, delete it
                if not self.priorityBuckets[slot.priority].cacheLineSize:
                    # if self.minPriorityHeap and self.minPriorityHeap[0] == slot.priority:
                    #     # remove the priority bucket from the priority minHeap
                    #     heappop(self.minPriorityHeap)
                    self.minExpirationHeap(self.priorityBuckets[slot.priority].heap_index)
                    del self.priorityBuckets[slot.priority]

                # add the slot to the new priority bucket 
                self.add_slot_to_head(slot, priority)
            return

        # key does not exist in the cache
        if not self.freeList:
            self.Evict(current_time)

        cache_slot = self.freeList.pop()
        cache_slot.initialize_slot(key, value, priority, current_time + expire)

        # add the slot to the head of the priority bucket
        self.add_slot_to_head(cache_slot, priority)
        self.hashMap[key] = cache_slot

        # add slot ot min expiry heap
        #O(logn)
        self.minExpirationHeap.add(MinHeapNode(cache_slot.expire, cache_slot))

    def SetMaxItems(self, max_items: int, current_time: int):
        if self.cacheSize > max_items:
            items_to_evict = self.cacheSize - max_items
            while items_to_evict:
                self.Evict(current_time=current_time)
                items_to_evict -= 1
            self.freeList = []
        elif self.cacheSize == max_items:
            self.freeList = []
        else:
            no_of_free_slots = max_items - self.cacheSize

            self.freeList = self.freeList[:no_of_free_slots]
        
        self.maxItems = max_items

    def Keys(self):
        return self.hashMap.keys()

# c = PriorityExpiryCache(5)
# c.Set("A", value=1, priority=5,  expire=100, current_time = 0)
# c.Set("B", value=2, priority=15, expire=3,  current_time = 0)
# c.Set("C", value=3, priority=5,  expire=10,  current_time = 0)
# c.Set("D", value=4, priority=1,  expire=15, current_time = 0)
# c.Set("E", value=5, priority=5,  expire=150, current_time = 0)
# print(c.Get("C", current_time=0))
# # Current time = 0
# c.SetMaxItems(5, current_time=0)
# print(c.Keys()) #["A", "B", "C", "D", "E"]
# # space for 5 keys, all 5 items are included
# # Current time = 5
# c.SetMaxItems(4, current_time=5)
# print(c.Keys()) # ["A", "C", "D", "E"]
# # // "B" is removed because it is expired.  expiry 3 < 5
# c.SetMaxItems(3, current_time=5)
# print(c.Keys()) # ["A", "C", "E"]
# # // "D" is removed because it the lowest priority
# # // D's expire time is irrelevant.
# c.SetMaxItems(2, current_time=5)
# print(c.Keys()) # ["C", "E"]
# # // "A" is removed because it is least recently used."
# # // A's expire time is irrelevant.
# c.SetMaxItems(1, current_time=5)
# print(c.Keys())
# # c.Keys() = ["C"]



c = PriorityExpiryCache(5)

c.Set(key="A", value=1, priority=5,  expire=3, current_time = 1)
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
