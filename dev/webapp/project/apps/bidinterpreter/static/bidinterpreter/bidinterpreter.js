var dropzone;
function setup() {
    createCanvas(200, 200);
    background(0);

    dropzone = select('#dropzone');
    dropzone.dragOver(highlight);

}

function highlight() {
    dropzone.style('background-color', '#ccc')

}