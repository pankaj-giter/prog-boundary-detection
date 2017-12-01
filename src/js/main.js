// define global variables
var prog_detector = null;
var clip_creator = null;
var current_program_detected_el = null

/* main function to bootstrap the underlying objects
*/
$(document).ready(function () {
    // initialize the label element
    current_program_detected_el = document.getElementById("current_detected_program");

    // initialize program detector
    prog_detector = new ProgramDetector("video", "canvas");
    prog_detector.subscribeToProgramChangedEvent(onProgramChanged);
    prog_detector.subscribeToProgramDetectedEvent(onProgramDetected);

    // TODO: Venki: initialize the clip creator module
    clip_creator = new ClipCreator("div_clips_panel");

    // player.js (for use by Ambika)
    //  TODO: Ambika: init the HLS.js player and subscribe to its events
});

/*
Event-handler that is triggered when the HLS.JS player begins playback of a new segment
 */
function PlaySegmentChanged(event, data){
    console.log("PlaySegment Changed: " + data.frag.url + " " + data.frag.duration);

    // call the Program Detector informing of a new segment that is now playing
    prog_detector.playSegmentChanged(new Segment(data.frag.url,data.frag.duration));
}

/*
This is an event-handler that is triggered when the 'Toggle Program Detection' button on the HTML page is clicked
 */
var _playSegmentChanged = PlaySegmentChanged;
function onToggleProgramDetection(){
    console.log("Toggling program detection...");
    prog_detector.toggleDetection();

    if (prog_detector.isDetectionEnabled()){
        // wire up the HLS.JS play_segment_changed event with the program detector
        Player.HLS.on(Hls.Events.FRAG_CHANGED,_playSegmentChanged);
    }
    else{
        // undo the wiring of the HLS.JS play_segment_changed event with the program detector
        Player.HLS.off(Hls.Events.FRAG_CHANGED,_playSegmentChanged);
    }
}

/*
Event-handler function that is triggered when a change in program is detected.
 */
function onProgramChanged(sender, program){
    console.log("%cProgram has changed", "color:blue");
    console.log(program);

    clip_creator.createClipForProgram(program);
}
function onProgramDetected(sender, program){
    console.log("%cProgram has been detected", "color:blue");
    console.log(program);
    current_program_detected_el.innerText = program.type;
}
