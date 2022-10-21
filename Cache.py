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
import heapq
from typing import Any
from typing import TypedDict

# Structure to hold each element of the cache
class CacheSlot:
    def __init__(self):
        self.key = ""
        self.val = None
        self.priority = 0
        self.expire = 0
        self.next = None
        self.prev = None
    
    def initializeSlot(self, key ="", val = 0, priority = 0, expiration = 0):
        self.key = key
        self.val = val
        self.priority = priority
        self.expire = expiration


class PriorityBucket:
    def __init__(self, priority = 0):
        self.priority = priority
        self.head = CacheSlot(key = "PriorityHead")
        self.tail = CacheSlot(key = "PriorityTail")
        self.head.next = self.tail
        self.tail.prev = self.head
        self.cacheLineSize = 0



class PriorityExpiryCache:

    def __init__(self, maxItems: int):
        self.maxItems = maxItems

        # number of filled CacheSlots
        self.cacheSize = 0

        # Simulation of Cache slots
        # If empty cache is full
        self.freeList = [CacheSlot(key = "FreeListHead") for i in range(maxItems)] 

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
        self.minExpirationHeap = list()
    

    def removeSlot(self, slot: CacheSlot, priority: int) -> None:

        priorityBucket = self.priorityBuckets[priority]

        if not priorityBucket.cacheLineSize:
            return

        # remove the slot from the list
        # connect the next and previous slots
        slot.prev.next = slot.next
        slot.next.prev = slot.prev
        slot.prev = slot.next = None
        priorityBucket.cacheLineSize -= 1




    def addSlotHead(self, slot:CacheSlot, priority: int) -> None:

        if slot.priority not in self.priorityBuckets:
            # create a new priority bucket
            self.priorityBuckets[priority] = PriorityBucket(priority)
            # insert the priority to the heap
            heapq.heappush(self.minPriorityHeap, priority)

        priorityBucket = self.priorityBuckets[slot.priority]

        # get the head of the cacheSlots in the priority bucket
        priorityBucketHead = priorityBucket.head

        # add slot to the list
        slot.next = priorityBucketHead.next
        slot.prev = priorityBucketHead

        priorityBucketHead.next.prev = slot
        priorityBucketHead.next = slot

        # increment the count of slots in this priority
        priorityBucket.cacheLineSize += 1


    def removeSlotFromTail(self, priority: int) -> None:

        if priority not in priorityBucket:
            return
        # remove a slot from the tail of the given priority
        priorityBucket = self.priorityBuckets[priority]
        # Check if the priority bucket contains any cache slots
        if not priorityBucket.cacheLineSize:
            return
        self.removeSlot(priorityBucket.tail.prev, priority)




    def Get(self, key:str, currentTime: int) -> tuple:
        
        # if the key exists in the cache, return the value only if it is not expired
        if key in self.hashMap:
            slot = self.hashMap[key]
            # Only return the value if the expiration time >= currentTime 
            if slot.expire >= currentTime:
                # move the slot to head of priority bucket
                self.removeSlot(slot, slot.priority)
                self.addSlotHead(slot, slot.priority)
                return (True, self.hashMap[key].val)

        # if the key does not exist return None
        return (False, None)

    
    def Set(self, key:str, val: Any, priority: int, expire: int, currentTime: int) -> None:
        
        # if the key already exists in the cache
        if key in self.hashMap:
            slot = self.hashMap[key]

            previous_priority = slot.priority
            
            # intialize the slot again
            slot.initializeSlot(key, val, priority, currentTime + expire)

            # check if the priority for this key is still the same
            if previous_priority == priority:

                # just do a get to tag this as recently accessed element and move it to the head of priority list
                self.Get(key, currentTime)

            else:

                # remove the slot from the previous priority
                self.removeSlot(slot, previous_priority)

                # add the slot to the new priority bucket 
                self.addSlotHead(slot, priority)

        # if key does not exist in the cache
        
        elif not self.freeList:
            self.Evict()
        
        cache_slot = self.freeList.pop()
        cache_slot.initializeSlot(key, val, priority, currentTime + expire)

        # add the slot to the head of the priority bucket
        self.addSlotHead(cache_slot, priority)


    










        
        






        
    # Get O(1)
    # Set log(n)

        # Check expiry
        # Check priority
        # Check LRU at given priority 
