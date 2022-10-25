from abc import abstractmethod
from typing import Any


class MinHeapNode:
    def __init__(self, min_heap_key: int = 0, min_heap_value: Any = None):
        self.key = min_heap_key
        self.node = min_heap_value


class MinHeap:
    def __init__(self):
        self.size = 0
        self.Heap = []

    def getLeftChildIndex(self, parent: int) -> int:
        """

        :param parent:
        :return:
        """
        return (parent*2) + 1

    def getRightChildIndex(self, parent: int) -> int:

        return parent * 2 + 2
    
    def getParentIndex(self, child: int) -> int:
        return (child- 1) // 2

    def hasLeftChild(self, parent: int) -> bool:
        return self.getLeftChildIndex(parent) < self.size
    
    def hasRightChild(self, parent: int) -> bool:
        return self.getRightChildIndex(parent) < self.size
    
    def hasParent(self, child: int) -> bool:
        return self.getParentIndex(child) >= 0
    
    def leftChild(self, parent: int) -> int:
        return self.Heap[self.getLeftChildIndex(parent)]
    
    def rightChild(self, parent: int) -> int:
        return self.Heap[self.getRightChildIndex(parent)]
    
    def parent(self, child: int) -> bool:
        return self.Heap[self.getParentIndex(child)]
    
    def swap(self, pos1, pos2):
        self.Heap[pos1], self.Heap[pos2] = self.Heap[pos2], self.Heap[pos1]

    def peek(self) -> None:
        if self.size == 0:
            return -1
        
        return self.Heap[0]
 
    def pop(self) -> None:
        if self.size == 0:
            return -1
        
        val = self.Heap[0]
        
        self.Heap[0] = self.Heap[self.size - 1]
        self.size -= 1
        self.Heap.pop()
        self.heapifyDown()
        return val
    
    def add(self, item: Any) -> None:        
        self.Heap.append(item)
        self.size += 1 
        self.heapifyUp()

    def delete(self, index: int) -> None:
       
        if index == self.size - 1:
            self.size -= 1
            # remove the last element O(1)
            self.Heap.pop()
            return
        # replace the index entry with the last element in the heap
        prev_key = self.Heap[index].key
        self.Heap[index] = self.Heap[-1]
        self.size -= 1
        # remove the last element O(1)
        self.Heap.pop()
        
        # if the new value in the index < previous value, we need to heapify up
        if self.Heap[index].key < prev_key:
            self.heapifyUp(index)
            
        # if the new value in the index > previous value, we need to heapify down
        elif self.Heap[index].key > prev_key:
            self.heapifyDown(index)
        # other wise there is no need to heapify as the values might have been the same
        self.Heap[index].node.heap_index = index
        
   
    def heapifyUp(self, index = -1) -> None:

        if index == -1:
            index = self.size - 1

        while self.hasParent(index) and self.parent(index).key > self.Heap[index].key:
            self.parent(index).node.heap_index = index
            self.swap(self.getParentIndex(index), index)
            index = self.getParentIndex(index)
        
        self.Heap[index].node.heap_index = index
        
    def heapifyDown(self, index = -1)-> None:

        if index == -1:
            index = 0

        # if there is no left child then there is definetly no right child
        # Heap is a complete binary tree. That is what helps in maintaing its property
        while (self.hasLeftChild(index)):
            # find the index of the smaller child among the two children
            smallerchild = self.getLeftChildIndex(index)
            if self.hasRightChild(index) and self.rightChild(index).key < self.leftChild(index).key:
                smallerchild = self.getRightChildIndex(index)
            # if the index already contains the smaller expiration time exit!
            if self.Heap[index].key < self.Heap[smallerchild].key:
                # mark where the slot is in the Expiration min heap
                self.Heap[index].node.heap_index = index
                return
            else:
                self.Heap[smallerchild].node.heap_index = index
                self.swap(index, smallerchild)
                index = smallerchild
         