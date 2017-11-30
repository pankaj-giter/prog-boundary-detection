// venki's Code

class ClipCreator{
    constructor(clips_panel_id){
        this._clips_panel_id = clips_panel_id;
        this._clips_panel_el = document.getElementById(this._clips_panel_id);
        this._clip_index = 0;
    }
    test(startURL, endURL, targetDuration){
        console.log(this._makePlaylist(startURL, endURL, targetDuration));
    }
    createClipForProgram(program){
        console.log(program.start_segment.url);
        console.log(program.end_segment.url);

        var clipHLSPlaylistM3U8 = this._makePlaylist(program.start_segment.url, program.end_segment.url, parseInt(program.start_segment.extinf_duration));

        this.postClipVideoM3U8(clipHLSPlaylistM3U8, "clip_" + (++this._clip_index) + ".m3u8");
        this.createClipVideo(program);
    }

    postClipVideoM3U8(clipM3U8, clipM3U8FileName){
        var clip_post_url = "http://localhost:8080/" + clipM3U8FileName;
        $.ajax({
            method: "POST",
            url: clip_post_url,
            data: clipM3U8
        })
            .done(function(data, textStatus, jqXHR) {
                console.log(textStatus);
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.log(textStatus + errorThrown);
            });
    }
    createClipVideo(program) {
        var clip_container = document.createElement("div");

        var clip_title = document.createElement("span");
        clip_title.innerHTML = program.type;

        var video = document.createElement("video");
        video.setAttribute("poster", program.image_url);

        clip_container.appendChild(clip_title);
        clip_container.appendChild(video);
        this._clips_panel_el.appendChild(clip_container);

        var hls = new Hls();
        hls.attachMedia(video);
    }

    /* Churn out the media segment between the start and end URL's */
    _makePlaylist(startURL,endURL,targetDuration){


        var playlist = [];
        playlist.push('#EXTM3U');
        playlist.push('#EXT-X-VERSION:4');
        playlist.push('#EXT-X-TARGETDURATION:' + targetDuration);
        playlist.push('#EXT-X-MEDIA-SEQUENCE:800');
        playlist.push("\r\n");

        // Identify the sequence numbering pattern
        console.log("start URL: " + startURL);
        console.log("end URL: " + endURL);
        var pos = startURL.lastIndexOf("/");
        var _startSegment = startURL.substr(pos+1);
        var startURLpath = startURL.slice(0,pos+1);

        console.log("startSegment:" + _startSegment);
        console.log("startURL:" + startURLpath);

        pos = endURL.lastIndexOf("/");
        var _endSegment = endURL.substr(pos+1);
        var _endURLpath = endURL.slice(0,pos+1);

        console.log("endSegment:" + _endSegment);
        console.log("endURL:" + _endURLpath);

        if (_endURLpath == startURLpath){
            console.log("No directory roll over, clip creation possible")
        }

        // search and find start segment number
        var seg_naming_pattern = /(.*?)(\d+)\.ts$/;
        var start_number_match_result = seg_naming_pattern.exec(_startSegment);
        var end_number_match_result = seg_naming_pattern.exec(_endSegment);

        var start_number = parseInt(start_number_match_result[2]);
        var end_number = parseInt(end_number_match_result[2]);
        for (var i=0; i+start_number <= end_number; i++){
            playlist.push('#EXTINF:' + targetDuration + ",");
            playlist.push(startURLpath + start_number_match_result[1] + (start_number + i + "").padStart(5, "0") + ".ts");
        }
        playlist.push("#EXT-X-ENDLIST");
        return playlist.join("\r\n");
    }
}