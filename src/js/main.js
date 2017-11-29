var prog_detector = null;

$(document).ready(function () {
    prog_detector = new ProgramDetector();
    console.log("Current state of program detection is: " + prog_detector.isDetectionEnabled());

    prog_detector.toggleDetection();
    console.log("Current state of program detection is: " + prog_detector.isDetectionEnabled());

    program = new Program(constants.CNN, new Segment("seg1.ts", 2), new Segment("seg2.ts", 2), "some.jpg");
    console.log(program.type);

    // bootstrap
    //  subscribing to the HLS.js events and then calling the prog_detector's handler

    // player.js (for use by Ambika)
    //  init the HLS.js player and subscribe to its events
});

// event handler for events fired by hls.js
function PlaySegmentChanged(){
    console.log("name of segment and it's properties");

    // TODO: call the prog_detector's specific function..for PC to decide
    // Example: prog_detector.playSegmentChanged();
}