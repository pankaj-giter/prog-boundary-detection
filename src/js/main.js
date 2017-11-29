// define global variables
var prog_detector = null;
var clip_creator = null;

/* main function to bootstrap the underlying objects
*/
$(document).ready(function () {
    // initialize program detector
    prog_detector = new ProgramDetector("test_video", "test_canvas");
    prog_detector.subscribeToProgramChangedEvent(onProgramChanged);

    // TODO: Venki: initialize the clip creator module
    clip_creator = new ClipCreator();


    // player.js (for use by Ambika)
    //  TODO: Ambika: init the HLS.js player and subscribe to its events
});

/*
Event-handler that is triggered when the HLS.JS player begins playback of a new segment
 */
function PlaySegmentChanged(){
    console.log("TODO: Ambika: name of segment and it's properties");

    // call the Program Detector informing of a new segment that is now playing
    prog_detector.playSegmentChanged();
}

/*
This is an event-handler that is triggered when the 'Toggle Program Detection' button on the HTML page is clicked
 */
function onToggleProgramDetection(){
    // PC: Though I have toggle program detection here directly, instead, we should
    // be wiring up the event of segment changed from HLS.JS with the Program Detector

    console.log("Toggling program detection...");
    prog_detector.toggleDetection();
    document.getElementById("prog_detection_status").textContent = prog_detector.isDetectionEnabled() ? "ON" : "OFF";

    if (prog_detector.isDetectionEnabled()){
        // TODO: Ambika: wire up the HLS.JS play_segment_changed event with the program detector
    }
    else{
        // TODO: Ambika: undo the wiring of the HLS.JS play_segment_changed event with the program detector
    }
}

/*
Event-handler function that is triggered when a change in program is detected.
 */
function onProgramChanged(sender, program){
    console.log(sender);
    console.log(program);

    // TODO: Venki: clip_creator.createClipForProgram(program);
}
