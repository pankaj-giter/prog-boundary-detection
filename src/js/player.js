/**
 *
 */

function handleCurrentPlaySegment(seg_url,seg_dur){
    console.debug("CHANGED frag url: "+seg_url);
    console.debug("CHANGED frag duration: "+seg_dur);

}

function playHLS(){
    console.log("start js");
    var video = document.getElementById("video");
    //var srcHls = "https://moctobpltc-i.akamaihd.net/hls/live/571983/tc/news2/hls_playlist1_rendition3.m3u8";
    var srcHls = document.getElementById("text_videoUrl").value;
    var videoSrcInHls = "https://www.jenrenalcare.com/upload/poanchen.github.io/sample-code/2016/11/17/how-to-play-mp4-video-using-hls/sample.m3u8";
    var videoSrcInMp4 = "https://www.jenrenalcare.com/upload/poanchen.github.io/sample-code/2016/11/17/how-to-play-mp4-video-using-hls/sample.mp4";
    if(Hls.isSupported()) {

        var hls = Player.HLS;
        hls.attachMedia(video);
        //hls.attachMedia(video);
        hls.on(Hls.Events.MEDIA_ATTACHED, function () {
            console.debug("video and hls.js are now bound together !");
            hls.loadSource(srcHls);
            hls.on(Hls.Events.MANIFEST_PARSED, function (event, data) {
                console.log("manifest loaded, found " + data.levels.length + " quality level");
                video.play();
            });

            hls.on(Hls.Events.FRAG_LOADED,function(event,data) {
                console.debug("load fragment url: "+data.frag.url);
            });
            //fired when fragment matching with current video position is changing
            hls.on(Hls.Events.FRAG_CHANGED,function(event,data) {
                handleCurrentPlaySegment(data.frag.url,data.frag.duration);
            });
        });
    }else{
        console.warn("Browser does NOT support MediaSourceExtensions !");
    }
}
var Player = { HLS: new Hls() };