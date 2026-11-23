import {forward} from "@/lib/proxy";
export const dynamic = "force-dynamic";
export const GET = () => forward("/openapi.json");
