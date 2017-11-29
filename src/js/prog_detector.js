/*
JS Module for Program Boundary Detection (that relies on Visual Recognition)
    Subscribe to HLS.JS 'current segment playing' event Pankaj Chaudhari
    Video Snapshot creator Pankaj Chaudhari
        periodic time basis create snapshot of video frame
    Sub-Module for Visual Recognition against AWS Yiliang Bao
        Polymorphic interface (if you want to get fancy) to that we can choose to talk to AWS or something else.
        Sending snapshot to backend web interface
        Handling response and process it as type of CNN program or not
    Maintain state of program boundary change Pankaj Chaudhari
    Fire event if program has changed Pankaj Chaudhari
        includes info of start and end segment name/url and type of program (enum of 'CNN' and 'non-CNN')
 */

class ProgramDetector {
    constructor(video_el_id, canvas_el_id) {
       this._detectionEnabled = false;
       this._screenshotTimer = null;
       this._video_el = document.getElementById(video_el_id);
       this._canvas_el = document.getElementById(canvas_el_id);
       this._previousProgram = null;
       this._currentProgram = null;
       this._program_changed_listeners = [];

       console.log("Initializing the Program Detector module...");
       console.log("Current state of program detection is: " + this.isDetectionEnabled());
    }
    /* begin - private section */
    _enableProgramDetection(){
        console.log("Enabling program detection");
        this._screenshotTimer = setInterval(this.detectProgramOfSegment.bind(this), 2000);
    }
    _disableProgramDetection(){
        console.log("Disabling program detection");
        clearInterval(this._screenshotTimer);
    }
    getVideoScreenshot(){
        var canvas = this._canvas_el;
        var video = this._video_el;
        var ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        var dataUri = canvas.toDataURL("image/jpeg");
        console.log(dataUri);
        return dataUri;
    }
    detectProgramOfSegment(segment){
        var _this = this;
        var imageDataUri = this.getVideoScreenshot();
        var jqxhr = $.ajax({
            method: "POST",
            url: "http://localhost:63342/some-url/end-point",
            data: imageDataUri
        })
            .done(function(xhr) { _this.onScreenshotAnalysisComplete(xhr, segment, imageDataUri) })
            .fail(function(xhr) { _this.onScreenshotAnalysisFailed(xhr, segment, imageDataUri) });
        // TODO: might need to post binary instead of base64 to server
        // TODO: XHR requires CORS support from remote server
    }
    onScreenshotAnalysisComplete(xhr, segment, imageDataUri){
        console.log(xhr, segment);
        console.log(xhr.getAllResponseHeaders());

        // TODO: read response to figure out the type of detected program
        var detectedProgram = this.readProgramFromResponse();
        console.log("Detected program " + detectedProgram + " for screenshot");
        this.onScreenshotProgramDetectionComplete(detectedProgram, segment, imageDataUri);
    }
    onScreenshotAnalysisFailed(xhr, segment, imageDataUri){
        console.log(xhr, segment);
        console.log(xhr.getAllResponseHeaders());

        // TODO: remove this temporary code
        this.onScreenshotAnalysisComplete(xhr, segment, imageDataUri);
    }
    readProgramFromResponse(){
        // TODO: temporary code till I read the actual response and decipher the type of program
        var r = Math.random();
        if (r < 0.5 ) {
            return constants.CNN;
        }
        return constants.non_CNN;
    }
    onScreenshotProgramDetectionComplete(program_type, segment, imageDataUri){
        // check if we don't have any state, i.e. this is the first ever program detected
        if(this._currentProgram == null){
            console.log("Assigning current program");
            this._currentProgram = new Program(program_type, segment, segment, imageDataUri);
        }
        // we have a program, so let's check if an identical program to our current program has been detected
        else if(this._currentProgram != null && this._currentProgram.type == program_type){
            console.log("updating end_segment of current program");
            this._currentProgram.end_segment = segment;
        }
        // we have a program, so let's check if a program different than current program has been detected
        else if(this._currentProgram != null && this._currentProgram.type != program_type){
            console.log("program change detected");
            this._previousProgram = this._currentProgram;
            this._currentProgram = new Program(program_type, segment, segment, imageDataUri);

            // fire an event that program has changed...by passing in this._previousProgram
            $(document).trigger("program_detector.program_changed_event", this._previousProgram);
        }
    }
    /* end - private section */

    /* begin - events */
    subscribeToProgramChangedEvent(listener){
        $(document).on("program_detector.program_changed_event", listener);
    }
    /* end - events */

    /* begin - public section */
    isDetectionEnabled() {
        return this._detectionEnabled;
    }
    toggleDetection() {
        console.log("Current state of program detection is: " + this.isDetectionEnabled());

        // reset state of program tracking
        this._previousProgram = this._currentProgram = null;

        // toggle internal state
        this._detectionEnabled = !this._detectionEnabled;

        // NOTE: this will need to be removed so that we don't rely on a timer, rather events fired from HLS.JS player
        if(this._detectionEnabled){
            this._enableProgramDetection();
        } else {
            this._disableProgramDetection();
        }

        console.log("Current state of program detection is: " + this.isDetectionEnabled());
    }
    playSegmentChanged(segment){
        console.log("Event fired from the HLS.js stating the segment that is currently playing");

        // take screenshot and then send to the AWS API
        if (this._detectionEnabled){
            this.detectProgramOfSegment(segment);
        }
    }
    /* end - public section */
}

class Program {
    constructor(type, start_segment, end_segment, image_url) {
        this.type = type;
        this.start_segment = start_segment;
        this.end_segment = end_segment;
        this.image_url = image_url;
    }
    get type(){
        return this._type;
    }
    set type(value){
        this._type = value;
    }
    get start_segment(){
        return this._start_segment;
    }
    set start_segment(value) {
        this._start_segment = value;
    }
    get end_segment(){
        return this._end_segment;
    }
    set end_segment(value) {
        this._end_segment = value;
    }
    get image_url(){
        return this._image_url;
    }
    set image_url(value) {
        this._image_url = value;
    }
}

class Segment {
    constructor(url, extinf_duration) {
        this.url = url;
        this.extinf_duration = extinf_duration;
    }
    get url(){
        return this._url;
    }
    set url(value){
        this._url = value;
    }
    get extinf_duration(){
        return this._extinf_duration;
    }
    set extinf_duration(value){
        this._extinf_duration = value;
    }
}

class Constants {
    constructor(){
        this.CNN = "CNN";
        this.non_CNN = "non-CNN";
    }
}
var constants = new Constants();
