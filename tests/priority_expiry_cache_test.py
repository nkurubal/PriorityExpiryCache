import unittest
from cache_priority_queue import *

class TestCache(unittest.TestCase):

    def test_get(self):
        """
        Testing Get function.
        """
        cache = PriorityExpiryCache(max_items = 10)
        cache.Set(key="A", value=1, priority=5,  expire=3, current_time = 1)
        cache.Set(key="B", value=2, priority=15, expire=3, current_time=1)

        # get should return the True along with value when the current time <= expire time(4 for B)
        result = cache.Get('B', current_time=3)

        self.assertTrue(result[0], msg="Failed! B is not expired, but cache returned False")
        self.assertEqual(2, result[1], msg="Incorrect value of B returned")

        # B expires now
        result = (False, None)
        self.assertEqual(result, cache.Get("B", 5), msg="B has expired, but cache still returns True")

        # Cache Miss
        result = cache.Get('D', current_time=4)
        self.assertFalse(result[0], msg = "Get retured True for a non-existent key")
    
    
    def test_remove_slot(self):
        """
        Testing remove_slot function
        """

        c = PriorityExpiryCache(max_items = 3)

        c.Set("A", value=1, priority=5,  expire=100, current_time = 0)
        c.Set("B", value=2, priority=15, expire=3,  current_time = 0)
        c.Set("C", value=3, priority=5,  expire=10,  current_time = 0)

        # remove key "A" from cache. remove_slot only removes the links of the slot.
        # It does not completely delete the slot. This is because we might just want to remove
        # the slot from a certain priority cache line to a differnt one
        c.remove_slot(c.key_map['A'], 5)
        #assert that the next and prev pointers of the slot are Null and the 

        self.assertIsNone(c.key_map['A'].next, msg="Oops! Looks like the next link was not removed for the cache slot")
        self.assertIsNone(c.key_map['A'].prev, msg = "Oops! Looks like the next link was not removed for the cache slot")

        self.assertEqual(c.cache_size, 2, "Invalid cache size")
    
    def test_add_slot_to_head(self):
        """
        Testing add_slot_to_head function.
        """
        c = PriorityExpiryCache(max_items = 3)

        c.Set("A", value=1, priority=5,  expire=100, current_time = 0)
        c.Set("B", value=2, priority=15, expire=3,  current_time = 0)
        
        new_cache_slot = CacheSlot("C", val = 3, priority = 5, expiration=30)

        # remember: add_slot_to_head does not add the key to cache. 
        # Rather it just appends the created(add to the key_map)/ existing cache slot to the head
        c.key_map["C"] = new_cache_slot

        # try to add new_cache_slot to the head of priority list 5
        c.add_slot_to_head(new_cache_slot, 5)

        priority_bucket = c.priority_buckets[5]
        self.assertEqual(priority_bucket.head.next, new_cache_slot, "Priority bucket head does not point to the new cache slot")
        self.assertEqual(c.cache_size, 3)
        self.assertEqual(priority_bucket.cache_line_size, 2, "Oops! Forgot to increment the cach_line_size for the priority?")


    def test_evict_slot_from_tail(self):
        """
        Testing evict_slot_from_tail function
        """
        c = PriorityExpiryCache(max_items = 3)

        c.Set("A", value=1, priority=15,  expire=100, current_time = 0)
        c.Set("B", value=2, priority=15, expire=3,  current_time = 0)

        # At this point A must be evicted, as A will be at the tail of cache line in priority 15
        # Eviction is guaranteed removal. Thus A must deleted from key_map. 
        # Respective decrements in number of cache line elements and cache size will be done the remove_slot function.

        c.evict_slot_from_tail(15)

        self.assertNotIn('A', c.Keys())
        self.assertIn('B', c.Keys())


    
    def test_set(self):
        """
        Testing Set function.
        Also testing is basic eviction is working.
        - Expired slots first
        - Lowest Priority
        - If multiple items in lowest priority, Least Recently Used element.
        """
        c = PriorityExpiryCache(max_items = 3)

        c.Set("A", value=1, priority=5,  expire=100, current_time = 0)
        c.Set("B", value=2, priority=15, expire=3,  current_time = 0)
        c.Set("C", value=3, priority=5,  expire=10,  current_time = 0)

        result = ['A', 'B', 'C']

        self.assertEqual(result, c.Keys(), msg="Expected return keys did not match list of keys returned by cache")

        c.Set("D", value = 4, priority=1, expire = 20, current_time=4)

        # B is expired, so the entries in cahce should be ["A", "C" and "D"]
        result = c.Keys()
        self.assertNotIn('B', result, msg="Key B still found in cache")

        # Cache is full and does not have any expired items.
        # D must be evicted because of lowest, expiration time does not matter. 
        c.Set("E", value=1, priority=20,  expire=100, current_time = 5)

        self.assertNotIn('D', c.Keys(), msg="Eviction policy error! Did not evict the least priority element.")

        c.Get('A', current_time=6)

        # Least priority is 5. Now 'A' is recently used in priority 5. 
        # E was recently added to prioty 15, not least. So C is the least recently used. 
        # Any addition of new key to slot should evict C from priority bucket 5. 
        # None of the slots have expired.

        c.Set("F", value="anything", priority=100,  expire=2, current_time = 7)

        self.assertNotIn('C', c.Keys(), msg="Eviction policy error! Did not evict the least recently used element from least priority bucket.")

        # Current time 10. Key F has expired.
        # In the next set call F must be evicted despite being of larget priority.

        c.Set("G", value="G", priority=1,  expire=20, current_time = 10)

        self.assertNotIn('F', c.Keys(), msg="Eviction policy error! Did not evict the expired item.")

    
    def test_correctness_given_testcase(self):
        """
        Testing if the given test cases are satisfied.
        """
        c = PriorityExpiryCache(5)
        c.Set("A", value=1, priority=5,  expire=100, current_time = 0)
        c.Set("B", value=2, priority=15, expire=3,  current_time = 0)
        c.Set("C", value=3, priority=5,  expire=10,  current_time = 0)
        c.Set("D", value=4, priority=1,  expire=15, current_time = 0)
        c.Set("E", value=5, priority=5,  expire=150, current_time = 0)
        # Get returns (True, 3)
        self.assertTrue(c.Get("C", current_time=0)[0])
        # Current time = 0
        c.SetMaxItems(5, current_time=0)
        self.assertEqual(len(c.Keys()), 5, msg="Incorrect number of keys returned.") 
        # ["A", "B", "C", "D", "E"]
        # space for 5 keys, all 5 items are included
        # Current time = 5
        # "B" is removed because it is expired.  expiry 3 < 5
        c.SetMaxItems(4, current_time=5)
        result = c.Keys() # ["A", "C", "D", "E"]

        # Check cache contains exactly 4 items
        self.assertEqual(len(result), 4, msg="Incorrect number of keys returned.")
        # check that B is evicted
        self.assertNotIn('B', result, msg="Eviction error! Expired item still in cache and not evicted.")
        
        c.SetMaxItems(3, current_time=5)
        # "D" is removed because it the lowest priority
        # D's expire time is irrelevant.
        result = c.Keys() # ["A", "C", "E"]
        
        # Check cache contains exactly 3 items
        self.assertEqual(len(result), 3, msg="Incorrect number of keys returned.") 
        # check that D is evicted
        self.assertNotIn('D', result, msg="Eviction error! Lowest priority cache item not evicted.")
        
        c.SetMaxItems(2, current_time=5)
        result = c.Keys() # ["C", "E"]
        # // "A" is removed because it is least recently used."
        # // A's expire time is irrelevant.
        
        # Check cache contains exactly 2 items
        self.assertEqual(len(result), 2, msg="Incorrect number of keys returned.") 
        # check that A is evicted
        self.assertNotIn('A', result, msg="Eviction error! Least recently used from lowest priority bucket not evicted.")

        c.SetMaxItems(1, current_time=5)
        result = c.Keys()
        # c.Keys() = ["C"]. C was recently used. Hence, E is evicted.

        # Check cache contains exactly 1 items
        self.assertEqual(len(result), 1, msg="Incorrect number of keys returned.") 
        # check that A is evicted
        self.assertNotIn('E', result, msg="Eviction error! Least recently used from lowest priority bucket not evicted.")


if __name__ == '__main__':
    unittest.main()
