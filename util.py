"""
Utility data structures: Stack, Queue, PriorityQueue.
"""
import heapq
from collections import deque


class Stack:
    def __init__(self):
        self.list = []

    def push(self, item):
        self.list.append(item)

    def pop(self):
        return self.list.pop()

    def is_empty(self):
        return len(self.list) == 0

    def __len__(self):
        return len(self.list)


class Queue:
    def __init__(self):
        self.list = deque()

    def push(self, item):
        self.list.append(item)

    def pop(self):
        return self.list.popleft()

    def is_empty(self):
        return len(self.list) == 0

    def __len__(self):
        return len(self.list)


class PriorityQueue:
    def __init__(self):
        self.heap = []
        self.count = 0

    def push(self, item, priority):
        entry = (priority, self.count, item)
        heapq.heappush(self.heap, entry)
        self.count += 1

    def pop(self):
        (_, _, item) = heapq.heappop(self.heap)
        return item

    def is_empty(self):
        return len(self.heap) == 0

    def __len__(self):
        return len(self.heap)


class PriorityQueueWithFunction(PriorityQueue):
    def __init__(self, priority_function):
        super().__init__()
        self.priority_function = priority_function

    def push(self, item):
        priority = self.priority_function(item)
        super().push(item, priority)
