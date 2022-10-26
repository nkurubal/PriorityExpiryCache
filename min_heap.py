"""
General MinHeap implemetation details learned and adapted from 
Cracking the coding interview Tutorial with Gayle Laakmann McDowell
https://youtu.be/t0Cq6tVNRBA
"""
from typing import Any


class MinHeapNode:
    def __init__(self, min_heap_key: int = 0, min_heap_value: Any = None):
        self.key = min_heap_key
        self.node = min_heap_value


class MinHeap:
    """
    0-indexed min heap implementation.
    data members:
        size: size of the heap.
        Heap: array to store the heap values.
    """
    def __init__(self):
        self.size = 0
        self.Heap = list()

    def __get_left_child_index(self, parent: int) -> int:
        """
        Returns the index of the left child

        @param parent: parent index
        @return index of left child
        """
        return (parent*2) + 1

    def __get_right_child_index(self, parent_index: int) -> int:
        """
        Returns the index of the right child

        @param parent_index: parent index
        @return index of right child
        """
        return parent_index * 2 + 2
    
    def __get_parent_index(self, child_index: int) -> int:
        """
        Returns the index of the parent for the given child index

        @param child_index: index of child
        @return index of the parent
        """
        return (child_index- 1) // 2

    def __has_left_child(self, index: int) -> bool:
        """
        Returns if the given index has a left child.

        @param index: index of parent
        @return True, if the child for the given index exists
                 else, False
        """
        return self.__get_left_child_index(index) < self.size
    
    def __has_right_child(self, index: int) -> bool:
        """
        Returns True if the given index has a right child.

        @param index: index of parent
        @return True, if the right child for the given index exists
                 else, False
        """
        return self.__get_right_child_index(index) < self.size
    
    def __has_parent(self, child: int) -> bool:
        """
        Returns True if the given index has a parent.

        @param child: index of child
        @return True if the parent for the child exists.
                else False
        """
        return self.__get_parent_index(child) >= 0
    
    def __left_child(self, parent: int) -> int:
        """
        Returns the value of the left child.

        @param parent: index of parent
        @return value of the left child.
        """
        return self.Heap[self.__get_left_child_index(parent)]
    
    def __right_child(self, parent: int) -> int:
        """
        Returns the value of the right child.

        @param parent: index of parent
        @return value of the right child
        """
        return self.Heap[self.__get_right_child_index(parent)]
    
    def __parent(self, child: int) -> bool:
        """
        Returns the value of the parent

        @param parent: index of the parent
        @return value of the parent
        """
        return self.Heap[self.__get_parent_index(child)]
    
    def __swap(self, index1, index2):
        """
        Swap the values for the given indexes in the heap.
        @param index1, index2 - indexes to be swapped
        """
        self.Heap[index1], self.Heap[index2] = self.Heap[index2], self.Heap[index1]

    def peek(self) -> None:
        """
        Returns the minimum/ top element in the heap.
        O(1) operation.
        """
        if self.size == 0:
            return -1
        
        return self.Heap[0]
 
    def pop(self) -> None:
        """
        removes the minimum element form the heap. 
        O(logN)
        """
        if self.size == 0:
            return -1
        
        val = self.Heap[0]
        # swap the 0th element with the last element.
        self.Heap[0] = self.Heap[self.size - 1]
        self.size -= 1
        # remove the last element. O(1)
        self.Heap.pop()

        # make the heap valid again
        self.__heapify_down()

        return val
    
    def add(self, item: Any) -> None:  
        """
        Add the given item to the heap.
        @param item: item to be inserted to the heap
        O(logN)
        """      
        self.Heap.append(item)
        self.size += 1 
        self.__heapify_up()

    def delete(self, index: int) -> None:
        """
        Delete the item in the given index.
        O(logN)
        @param index: index to be deleted
        """
        if index == self.size - 1:
            self.size -= 1
            # remove the last element O(1)
            self.Heap.pop()
            return
        
        if index == 0:
            return self.pop()

        # replace the index entry with the last element in the heap
        prev_key = self.Heap[index].key
        self.Heap[index] = self.Heap[-1]
        self.size -= 1
        # remove the last element O(1)
        self.Heap.pop()
        
        # if the new value in the index < previous value, we need to heapify up
        if self.Heap[index].key < prev_key:
            self.__heapify_up(index)
            
        # if the new value in the index > previous value, we need to heapify down
        elif self.Heap[index].key > prev_key:
            self.__heapify_down(index)
        # other wise there is no need to heapify as the values might have been the same
        self.Heap[index].node.heap_index = index
        
   
    def __heapify_up(self, index = -1) -> None:
        """
        Bubble up until value is at its right position i.e parent is less than the current value.
        O(logN)
        @param index: index to heapify up from
        """
        if index == -1:
            index = self.size - 1

        while self.__has_parent(index) and self.__parent(index).key > self.Heap[index].key:
            self.__parent(index).node.heap_index = index
            self.__swap(self.__get_parent_index(index), index)
            index = self.__get_parent_index(index)
        
        self.Heap[index].node.heap_index = index
        
    def __heapify_down(self, index = -1)-> None:
        """
        Bubble down until value is at its right position i.e children are greater than the current value.
        O(logN)
        @param index: index to heapify up from 
        """
        if index == -1:
            index = 0

        # if there is no left child then there is definetly no right child
        # Heap is a complete binary tree. That is what helps in maintaing its property
        while (self.__has_left_child(index)):
            # find the index of the smaller child among the two children
            smallerchild = self.__get_left_child_index(index)
            if self.__has_right_child(index) and self.__right_child(index).key < self.__left_child(index).key:
                smallerchild = self.__get_right_child_index(index)
            # if the index already contains the smaller expiration time exit!
            if self.Heap[index].key < self.Heap[smallerchild].key:
                # mark where the slot is in the Expiration min heap
                self.Heap[index].node.heap_index = index
                return
            else:
                self.Heap[smallerchild].node.heap_index = index
                self.__swap(index, smallerchild)
                index = smallerchild
         