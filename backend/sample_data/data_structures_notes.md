# Course Notes: Data Structures & Trees

## Binary Search Trees (BST)
A Binary Search Tree is a binary tree data structure where each node satisfies the BST invariant: the key in any node is strictly greater than all keys stored in its left subtree, and strictly less than or equal to all keys stored in its right subtree.

In an average balanced BST, search, insertion, and deletion operate in O(log n) time. In the worst-case degenerate tree (a linked-list structure), these operations degrade to O(n) linear time.

## Binary Heaps
A binary heap is a complete binary tree that satisfies the heap property: in a max-heap, parent >= children; in a min-heap, parent <= children. Building a binary heap from an unsorted array takes O(n) linear time using Floyd's bottom-up heap construction algorithm.
