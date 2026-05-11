def heapify(arr, n, i):
    largest = i  # 初始化最大值为根节点
    left = 2 * i + 1     # 左子节点
    right = 2 * i + 2    # 右子节点

    # 如果左子节点存在且大于根节点
    if left < n and arr[left] > arr[largest]:
        largest = left

    # 如果右子节点存在且大于当前最大值
    if right < n and arr[right] > arr[largest]:
        largest = right

    # 如果最大值不是根节点，则交换并继续调整堆
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        heapify(arr, n, largest)


def heap_sort(arr):
    n = len(arr)

    # 构建最大堆（从最后一个非叶子节点开始）
    for i in range(n // 2 - 1, -1, -1):
        heapify(arr, n, i)

    # 逐个提取元素进行排序
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]  # 将根节点与末尾元素交换
        heapify(arr, i, 0)  # 重新调整堆

# 测试示例
if __name__ == "__main__":
    example_array = [64, 34, 25, 12, 22, 11, 90]
    print("原始数组：", example_array)
    heap_sort(example_array)
    print("排序后数组：", example_array)
