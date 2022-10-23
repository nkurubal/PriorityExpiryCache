"""
1. Min Heap - as discussed. Every element of the heap represents a single priority. Every element of the heap in turn points to a doubly LL of type X. The heap itself holds priority, head and tail pointers.
2. Free List - A LL of type X which holds all the free slots in the cache.
3. Hash Map - A mapping between hash(key) --> slot in cache.
4. Type X: Represents a single line/slot in the cache. Holds next and prev pointers.

GET(key):
> Perform hashing on key k to get h(k).
> Lookup h(k) in hash map. 
> If present, return value in hash_map[h(k)]
> To  update LRU, you can use the next and prev pointers + head/tail pointers.

SET(key, value, priority)
> Lookup head of free list.
> If not empty, pop from head.
> Lookup priority in heap ( log(n) )
> Append popped element to tail of heap.
> Add hash map entry of h(k) --> line of type X.
> Else if empty, pop element from min heap top. If top becomes empty, pop top.
> Add popped element to free list.
> Repeat steps 2, 3, 4, 5.
"""

# Get O(1)
# Set log(n)

# Check expiry
# Check priority
# Check LRU at given priority

from heapq import heappop, heappush
from typing import Any


# Structure to hold each element of the cache
class CacheSlot:
    def __init__(self, key: str = "", val: Any = 0, priority: int = 0, expiration:int = 0):
        self.key = key
        self.val = val
        self.priority = priority
        self.expire = expiration
        self.next = None
        self.prev = None

    def initialize_slot(self, key="", val=0, priority=0, expiration=0):
        self.key = key
        self.val = val
        self.priority = priority
        self.expire = expiration


class PriorityBucket:
    def __init__(self, priority=0):
        self.priority = priority
        self.head = CacheSlot(key="PriorityHead")
        self.tail = CacheSlot(key="PriorityTail")
        self.head.next = self.tail
        self.tail.prev = self.head
        self.cacheLineSize = 0


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
        self.minPriorityHeap = list()

        # Priority Queue to maintain the expiriation time of each cache slot
        # if the current time > expirationTime evict the slot during eviction
        # [(expiryTime, CacheSlot)] 
        self.minExpirationHeap = list()

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
            heappush(self.minPriorityHeap, priority)

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
            return

        # get the least recently used cache slot
        slot_to_evict = priority_bucket.tail.prev

        self.remove_slot(slot_to_evict, priority)

        # if the priority bucket becomes empty
        if not priority_bucket.cacheLineSize:
            # check if this was the least priority in the system
            # if yes then, pop it from the heap
            # Time Complexity: O(logn)
            if self.minPriorityHeap and self.minPriorityHeap[0] == priority:
                # remove the priority bucket from the priority minHeap
                heappop(self.minPriorityHeap)

        # add the slot back to free lists
        self.freeList.append(slot_to_evict)

        # remove the key from the hashMap
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
        # why while? there maybe some invalid equiry times in the heap as a result of update operation.
        while self.minExpirationHeap and self.minExpirationHeap[0][0] < current_time:
            # pop the heap
            expire_time, cache_slot = heappop(self.minExpirationHeap)

            # check if the expired key has already been evicted from the cache
            if cache_slot.key not in self.hashMap:
                continue
            
            # the slot might have been updated. So this expireTime is not valid
            # continue the search
            if expire_time != cache_slot.expire:
                continue
            # remove the slot
            self.remove_slot(cache_slot, cache_slot.priority)
                    # if the priority bucket becomes empty, delete it
            if not self.priorityBuckets[cache_slot.priority].cacheLineSize:
                if self.minPriorityHeap and self.minPriorityHeap[0] == cache_slot.priority:
                    # remove the priority bucket from the priority minHeap
                    heappop(self.minPriorityHeap)

            # add the slot back to free lists
            self.freeList.append(cache_slot)

            # remove the key from the hashMap
            del self.hashMap[cache_slot.key]
            # evicted a slot so return
            return

        # No slots have expired, so evict LRU cache slot from the lowest priority bucket
        while self.minPriorityHeap and self.priorityBuckets[self.minPriorityHeap[0]].cacheLineSize == 0:
            heappop(self.minPriorityHeap)
        
        if self.minPriorityHeap:
            min_priority = self.minPriorityHeap[0]
            self.evict_slot_from_tail(min_priority)
        else:
            print("Evict error, this should not have happended")

    def Set(self, key: str, val: Any, priority: int, expire: int, current_time: int) -> None:

        # if the key already exists in the cache
        if key in self.hashMap:

            slot = self.hashMap[key]

            previous_priority = slot.priority

            # initialize the slot again with new values
            slot.initialize_slot(key, val, priority, current_time + expire)

            # check if the priority for this key is still the same
            if previous_priority == priority:

                # just do a get to mark this as a recently accessed element and move it to the head of priority list
                self.Get(key, current_time)

            else:

                # remove the slot from the previous priority
                self.remove_slot(slot, previous_priority)
                # if the priority bucket becomes empty, delete it
                if not self.priorityBuckets[slot.priority].cacheLineSize:
                    if self.minPriorityHeap and self.minPriorityHeap[0] == slot.priority:
                        # remove the priority bucket from the priority minHeap
                        heappop(self.minPriorityHeap)

                # add the slot to the new priority bucket 
                self.add_slot_to_head(slot, priority)
            # O(logn) - push the new expiry time to the expiration heap
            # This will be a duplicate entry. The previous (expire, slot) might have expired during eviction.
            # But that will not be a valid slot to evict eviction. Hence, needs to be checked during eviction
            heappush(self.minExpirationHeap, (slot.expire, slot))
            return

        # key does not exist in the cache
        if not self.freeList:
            self.Evict(current_time)

        cache_slot = self.freeList.pop()
        cache_slot.initialize_slot(key, val, priority, current_time + expire)

        # add the slot to the head of the priority bucket
        self.add_slot_to_head(cache_slot, priority)
        self.hashMap[key] = cache_slot

        heappush(self.minExpirationHeap, (cache_slot.expire, cache_slot))


c = PriorityExpiryCache(5)

c.Set(key="A", val=1, priority=5,  expire=100, current_time = 0)
c.Set(key="B", val=2, priority=15, expire=3, current_time=1)
print(c.Get("B", current_time=3))
c.Set(key="C", val = "blah", priority=5, expire= 40, current_time = 6)
print(c.Get(key = "A", current_time=7))
c.Set(key="D", val = 3, priority=20, expire = 50, current_time= 7)
print(c.Get(key="B", current_time=8))
c.Set(key="A", val=1, priority=20,  expire=100, current_time = 9)
c.Set(key="C", val = "blah", priority=20, expire= 40, current_time = 10)
c.Set(key="E", val = 'E', priority=20, expire= 40, current_time = 11)
print("No eviction till this point")
print(c.Get(key= "B", current_time=11))
print(c.Get(key= "A", current_time=11))
print(c.Get(key= "C", current_time=11))
print(c.Get(key= "D", current_time=11))
print(c.Get(key= "E", current_time=11))

print("Eviction Starts")
c.Set(key="G", val=2, priority=20, expire=70, current_time=13)
print(c.Get(key= "B", current_time=13))
c.Set(key="F", val=2, priority=1, expire=70, current_time=14)
print(c.Get(key= "G", current_time=11))
print(c.Get(key= "A", current_time=11))
print(c.Get(key= "C", current_time=11))
print(c.Get(key= "D", current_time=11))
print(c.Get(key= "E", current_time=11))