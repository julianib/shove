import { useState } from "react";

import { makeStyles } from "@material-ui/core/styles";

import { socket } from "../connection";

const { REACT_APP_BACKEND_URL } = process.env;

const useStyles = makeStyles((theme) => ({
  status: {
    padding: "10px",
    borderRadius: "10px 0px 0px",
    texAlign: "center",
    cursor: "pointer",
  },
}));

let deaf = true;

function ConnectionStatus() {
  const [status, setStatus] = useState();

  const classes = useStyles();

  var removeTimer;

  function removeStatus() {
    clearTimeout(removeTimer);
    setStatus();
  }

  function popup(text, color) {
    clearTimeout(removeTimer);
    setStatus({
      text,
      color,
    });
    removeTimer = setTimeout(removeStatus, 5000);
  }

  if (deaf) {
    deaf = false;

    socket.on("connect", () => {
      popup("Connected!", "green");
    });

    socket.on("connect_error", () => {
      popup(`Could not connect to '${REACT_APP_BACKEND_URL}'`, "darkred");
    });

    socket.on("disconnect", (reason) => {
      popup("Disconnected: " + reason, "darkred");
    });
  }

  return status ? ( // if no status is set, hide the div
    <div
      onClick={removeStatus}
      style={{ backgroundColor: status.color }}
      className={classes.status}
    >
      {status.text}
    </div>
  ) : null;
}

export default ConnectionStatus;
