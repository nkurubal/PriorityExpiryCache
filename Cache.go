package Cache

import "time"

type PriorityExpiryCache struct {
	maxItems int
	// TODO(interviewee): implement this
}

func NewCache(maxItems int) *PriorityExpiryCache {
	return &PriorityExpiryCache{
		maxItems: maxItems,
	}
}

func (c *PriorityExpiryCache) Get(key string) interface{} {
	return nil
}

func (c *PriorityExpiryCache) Set(key string, value interface{}, priority int, expire time.Time) {
	// ... the interviewee does not need to implement this.

	c.evictItems()
}

func (c *PriorityExpiryCache) SetMaxItems(maxItems int) {
	c.maxItems = maxItems

	c.evictItems()
}

// evictItems will evict items from the cache to make room for new ones.
func (c *PriorityExpiryCache) evictItems() {
}
