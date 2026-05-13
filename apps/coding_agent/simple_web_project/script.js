// 简单的JavaScript功能：在页面加载完成后弹出欢迎消息
window.onload = function() {
    alert('欢迎访问简单Web项目！');
};

// 可选：为页面上的标题添加点击事件响应
document.querySelector('h1').addEventListener('click', function() {
    alert('你点击了标题！');
});