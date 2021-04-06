import { useState, useRef } from "react";

import Button from "@material-ui/core/Button";
import Slider from "@material-ui/core/Slider";

import { socket, sendPacket } from "../connection";
import { secondsToString, percentage } from "../formatting";
import { Typography } from "@material-ui/core";

let deaf = true;

// const useAudio = (url) => {
//     const [audio] = useState(new Audio(url));
//     const [playing, setPlaying] = useState(false);

//     const toggle = () => setPlaying(!playing);

//     useEffect(() => {
//         playing ? audio.play() : audio.pause();
//     }, [playing, audio]);

//     useEffect(() => {
//         audio.addEventListener("ended", () => setPlaying(false));
//         return () => {
//             audio.removeEventListener("ended", () => setPlaying(false));
//         };
//     }, [audio]);

//     return [playing, toggle];
// };

function AudioPlayer() {
    const [source, setSource] = useState();
    const [volume, setVolume] = useState(0.25);
    const [playing, setPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const [duration, setDuration] = useState(0.1); // prevent ZeroDivision in the future (x% done ratios)
    const [loop, setLoop] = useState(false);

    const audioRef = useRef();

    if (deaf) {
        deaf = false;

        socket.on("play_audio", (packet) => {
            console.debug("> play_audio", packet);
            loadNewAudio(packet.url);
        });

        // socket.on audio_data, loop enable/disable, play/pause, new url (with author)
    }

    const loadNewAudio = (url) => {
        setSource(url);
        // if (audioRef.current) {
        // how does this work
        audioRef.current.load(); // tell element to load new source
        audioRef.current.play();
        // }
    };

    function onChangeVolumeSlider(e, value) {
        // client side volume control
        setVolume(value);

        // if (audioRef.current) {
        audioRef.current.volume = Number(value);
        // }
    }

    function onClickToggleLoop() {
        // should send packet
        audioRef.current.loop = !loop;
        setLoop(!loop);
    }

    function onClickTogglePlay() {
        // should send packet
        if (playing) {
            audioRef.current.pause();
        } else {
            audioRef.current.play();
        }
        setPlaying(!playing);
    }

    // https://developer.mozilla.org/en-US/docs/Web/HTML/Element/audio#events

    function onDurationChange(e) {
        console.log("durationchange", e);
        setDuration(Math.floor(e.target.duration));
    }

    function onEmptied(e) {
        console.log("emptied", e);
    }

    function onEnded(e) {
        console.log("ended", e);
    }

    function onPause(e) {
        console.log("pause", e);
        setPlaying(false);
    }

    function onPlay(e) {
        console.log("play", e);
        setPlaying(true);
        // make sure html element's volume is correct
        audioRef.current.volume = volume;
    }

    function onTimeUpdate(e) {
        // console.log("timeupdate", e); // spams console
        setProgress(Math.floor(e.target.currentTime));
    }

    function onWaiting(e) {
        console.log("waiting", e);
    }

    return (
        <>
            <Typography>{`${secondsToString(progress)} / ${secondsToString(
                duration
            )}`}</Typography>
            <Button
                variant="outlined"
                color="secondary"
                onClick={onClickTogglePlay}
            >
                {playing ? "Pause" : "Play"}
            </Button>
            <Button
                variant="outlined"
                color="secondary"
                onClick={onClickToggleLoop}
            >
                Loop: {loop ? "ye" : "no"}
            </Button>
            <Slider
                className="bet-slider"
                min={0}
                max={1}
                step={0.05}
                value={volume}
                onChange={onChangeVolumeSlider}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => percentage(value)}
            />
            <Button
                variant="outlined"
                color="secondary"
                onClick={() => sendPacket("get_audio", {})}
            >
                Get live
            </Button>

            {/*todo Should just be an Audio() object, no html required*/}
            <audio
                controls
                loop={loop}
                ref={audioRef}
                onDurationChange={onDurationChange}
                onEmptied={onEmptied}
                onEnded={onEnded}
                onPause={onPause}
                onPlay={onPlay}
                onTimeUpdate={onTimeUpdate}
                onWaiting={onWaiting}
            >
                {/*breaks without this <source />*/}
                <source src={source} />
            </audio>
        </>
    );
}

export default AudioPlayer;