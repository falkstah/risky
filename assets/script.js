/*used to move chat-controls by mouse movement*/

/*test */
console.log("JS geladen!");

document.addEventListener("DOMContentLoaded", function () {
    const panel = document.querySelector(".chart-controls");
    let isDragging = false;
    let offsetX = 0;
    let offsetY = 0;

    panel.addEventListener("mousedown", function (e) {
        isDragging = true;
        offsetX = e.clientX - panel.offsetLeft;
        offsetY = e.clientY - panel.offsetTop;
    });

    document.addEventListener("mousemove", function (e) {
        if (isDragging) {
            panel.style.left = (e.clientX - offsetX) + "px";
            panel.style.top = (e.clientY - offsetY) + "px";
        }
    });

    document.addEventListener("mouseup", function () {
        isDragging = false;
    });
});
