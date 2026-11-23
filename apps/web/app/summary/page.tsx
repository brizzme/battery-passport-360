import {permanentRedirect} from "next/navigation";

// The PoC summary is the home page; keep old /summary links working.
export default function Summary() {
  permanentRedirect("/");
}
