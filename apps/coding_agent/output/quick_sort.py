import random
from typing import List

def quick_sort(arr: List[int], low: int = 0, high: int = None) -> None:
    """
    快速排序主函数，对给定列表的子数组进行原地排序。
    
    Args:
        arr: 待排序的整数列表。
        low: 子数组起始索引。
        high: 子数组结束索引。
    """
    # 处理空列表或无效输入
    if not arr or len(arr) <= 1:
        return
    
    if high is None:
        high = len(arr) - 1
    
    if low < high:
        # 随机选择枢轴以避免最坏情况性能
        pivot_index = partition(arr, low, high)
        quick_sort(arr, low, pivot_index - 1)
        quick_sort(arr, pivot_index + 1, high)


def partition(arr: List[int], low: int, high: int) -> int:
    """
    将数组分为两部分：小于等于枢轴的在左，大于枢轴的在右。
    
    Args:
        arr: 待分区的列表。
        low: 起始索引。
        high: 结束索引。
    
    Returns:
        枢轴最终位置的索引。
    """
    # 随机选择一个元素作为枢轴，并与最后一个元素交换
    random_index = random.randint(low, high)
    arr[random_index], arr[high] = arr[high], arr[random_index]
    
    pivot = arr[high]
    i = low - 1
    
    for j in range(low, high):
        if arr[j] <= pivot:
            i += 1
            arr[i], arr[j] = arr[j], arr[i]
    
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1

# 示例用法：
if __name__ == "__main__":
    test_arr = [3, 6, 8, 10, 1, 2, 1]
    print("Original array:", test_arr)
    quick_sort(test_arr)
    print("Sorted array:   ", test_arr)