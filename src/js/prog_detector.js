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

var image_recognition_url_template = "http://localhost:8000/tech-jam/";

class ProgramDetector {
    constructor(video_el_id, canvas_el_id) {
       this._detectionEnabled = false;
       this._screenshotTimer = null;
       this._video_el = document.getElementById(video_el_id);
       this._canvas_el = document.getElementById(canvas_el_id);
       this._previousProgram = null;
       this._currentProgram = null;
       this._program_detection_in_progress = false;

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
        return dataUri;
    }
    fromImageDataUriToBinary(imageDataUri){
        // imageDataUri is of the form data:image/jpeg;base64,/9j/4AAQSkZJ...
        var parts = imageDataUri.split(";base64,");
        //console.log(parts[0]);
        //console.log(parts[1]);

        // https://developer.mozilla.org/en-US/docs/Web/API/WindowBase64/Base64_encoding_and_decoding
        return atob(parts[1]);
    }
    detectProgramOfSegment(segment){
        var _this = this;
        // TODO: change file extension from .ts to .jpeg
        var image_recognition_url = image_recognition_url_template + segment.url.substring(segment.url.lastIndexOf("/") + 1);
        var imageDataUri = this.getVideoScreenshot();
        console.debug("Following is screenshot of segment %s", segment.url);
        console.debug(imageDataUri);

        $.ajax({
            method: "POST",
            url: image_recognition_url,
            data: imageDataUri
        })
            .done(function(data, textStatus, jqXHR) {
                _this.onScreenshotAnalysisComplete(data, textStatus, jqXHR, segment, imageDataUri) })
            .fail(function(jqXHR, textStatus, errorThrown) {
                _this.onScreenshotAnalysisFailed(jqXHR, textStatus, errorThrown, segment, imageDataUri) })
            .always(function(){
                _this._program_detection_in_progress = false;
            })
    }
    onScreenshotAnalysisComplete(data, textStatus, jqXHR, segment, imageDataUri){
        console.debug(jqXHR, segment);
        console.debug(jqXHR.getAllResponseHeaders());

        // read response to figure out the type of detected program
        var detectedProgram = this.readProgramFromResponse(jqXHR);
        console.log("%cDetected program %s for screenshot of segment %s", "color: blue, font-size: large", detectedProgram, segment.url);
        this.onScreenshotProgramDetectionComplete(detectedProgram, segment, imageDataUri);
    }
    onScreenshotAnalysisFailed(jqXHR, textStatus, errorThrown, segment, imageDataUri){
        console.debug(jqXHR, segment);
        console.debug(jqXHR.getAllResponseHeaders());
    }
    readProgramFromResponse(jqXHR){
        var program = jqXHR.getResponseHeader("Akamai-Program-Detection");
        console.debug("Detected program returned back from backend server is '" + program + "'");
        if (program){
           if (program.startsWith("CNN")){
               return constants.CNN;
           }
        }
        else{
            console.warn("No detected program was returned in response from backend server");
            return constants.indeterminate;
        }
        return constants.non_CNN;
    }
    onScreenshotProgramDetectionComplete(program_type, segment, imageDataUri){
        // check if we don't have any state, i.e. this is the first ever program detected
        if(this._currentProgram == null){
            console.debug("Assigning current program");
            this._currentProgram = new Program(program_type, segment, segment, imageDataUri);

            // fire an event stating the 'program' that has been detected
            $(document).trigger("program_detector.program_detected_event", this._currentProgram);
        }

        // we have a program, so let's check if an identical program to our current program has been detected
        else if(this._currentProgram != null && (this._currentProgram.type == program_type || program_type == constants.indeterminate)){
            console.debug("updating end_segment of current program");
            this._currentProgram.end_segment = segment;

            // fire an event stating the 'program' that has been detected
            $(document).trigger("program_detector.program_detected_event", this._currentProgram);
        }

        // we have a program, so let's check if a program different than current program has been detected
        else if(this._currentProgram != null && this._currentProgram.type != program_type){
            console.debug("program change detected");
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
    subscribeToProgramDetectedEvent(listener){
        $(document).on("program_detector.program_detected_event", listener);
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
        /*
        if(this._detectionEnabled){
            this._enableProgramDetection();
        } else {
            this._disableProgramDetection();
        }
        */

        console.log("Current state of program detection is: " + this.isDetectionEnabled());
    }
    playSegmentChanged(segment){
        console.debug("Event fired from the HLS.js stating the segment that is currently playing");

        // take screenshot and then send to the AWS API
        if (this._detectionEnabled){

            if(this._program_detection_in_progress){
                console.log("%cSkipping program detection for segment %s as there is an outstanding detection", "color:darkmagenta", segment.url);
                return;
            }
            this._program_detection_in_progress = true;
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
        this.indeterminate = "indeterminate";
    }
}
var constants = new Constants();
