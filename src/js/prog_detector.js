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

       console.log("Initializing Program Detector...");
       console.log("Current state of program detection is: " + this.isDetectionEnabled());
    }
    isDetectionEnabled() {
        return this._detectionEnabled;
    }
    toggleDetection() {
        console.log("Current state of program detection is: " + this.isDetectionEnabled());

        this._detectionEnabled = !this._detectionEnabled;
        if(this._detectionEnabled){
            console.log("Enabling program detection");
            this._screenshotTimer = setInterval(this.detectProgram.bind(this), 2000);
        } else {
            console.log("Disabling program detection");
            clearInterval(this._screenshotTimer);
        }

        console.log("Current state of program detection is: " + this.isDetectionEnabled());
    }
    playSegmentChanged(){
        console.log("Event fired from the HLS.js stating the segment that is currently playing");
        // TODO: take screenshot and then send to the AWS API
    }
    detectProgram(){
        var canvas = this._canvas_el;
        var video = this._video_el;
        var ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        var dataUri = canvas.toDataURL("image/jpeg");
        console.log(dataUri);
    }
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
