"""WAD reminder parser: turns a reminder into hazards, direction, distance and action. Also used for Qwen's replies."""

import re

CATEGORIES = {
    "pedestrian": r"pedestrians?(?! (?:staircase|stairs|crossing|street|path|bridge|zone|area|overpass|underpass))|people|person|persons|passers?\s*-?\s*by|passerby|crowds?|man|men|woman|women|kids?|child(?:ren)?|someone|tourists?",
    "vehicle": r"cars?|vehicles?|taxis?|bus(?:es)?|trucks?|vans?|tricycles?|light rail|trams?|trains?|traffic(?! lights?)",
    "two_wheeler": r"bicycles?|bikes?|cyclists?|cycling|motorcycles?|motorbikes?|scooters?|electric (?:vehicle|bike)s?|e-?bikes?",
    "pole": r"(?:telegraph |utility |electric |lamp |light |street ?light |street ?lamp )?poles?|pillars?|posts?|columns?|street ?lamps?|street ?lights?|lamp ?posts?|traffic lights?",
    "tree_plant": r"trees?|trunks?|branch(?:es)?|plants?|flowers?|bush(?:es)?|flower ?beds?|flower ?pots?|green ?belts?",
    "sign": r"(?:stop |traffic |road |street )?signs?|signboards?|billboards?|boards?",
    "fence_railing": r"fences?|barbed wire|wires?|railings?|guard ?rails?|handrails?",
    "barrier_cone": r"road ?blocks?|barriers?|cones?|bollards?|obstacles?|roadblocks?",
    "furniture_stall": r"stalls?|stands?|chairs?|seats?|desks?|tables?|bench(?:es)?|cabinets?|shel(?:f|ves)|booths?|kiosks?|rest area|vendors?|carts?",
    "stairs_step": r"stairs?|staircases?|escalators?|(?<!\d )(?<!one |two |ive |ten |een |nty |rty |our |ree |ven |ght |ine |lve )steps?(?! away| ahead| in front| on the left| on the right| to the)",
    "curb_edge": r"curbs?|kerbs?|road ?edges?|edge of the road|roadside",
    "water": r"water|river|lake|canal|pond|puddles?|fountains?|sea",
    "hole_uneven": r"holes?|pits?|speed ?bumps?|potholes?|uneven|bumpy|manholes?",
    "wall_door": r"walls?|doors?|gates?|glass|buildings?|stores?|shops?|houses?",
    "animal": r"dogs?|cats?|birds?|pigeons?",
    "construction": r"construction|under repair|scaffold(?:ing)?",
    "street_object": r"vending machines?|machines?|trash ?cans?|rubbish bins?|bins?|garbage|box(?:es)?|statues?|sculptures?|hydrants?|mailbox(?:es)?|luggage|suitcases?|trolleys?|strollers?",
    "off_route": r"deviat\w*|back to the main (?:route|road)|return to the main (?:route|road)",
    "junction": r"intersections?|trifurcations?|bifurcations?|crossroads?|forks?|three\s*-?\s*way|zebra crossings?|crosswalks?|crossings?",
    "narrow_crowded": r"narrow|crowded|congested|congestion|heavy (?:pedestrian|traffic|people) flow|many people",
}
NUMW = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
}
NUM = r"\d{1,2}|" + "|".join(sorted(NUMW, key=len, reverse=True))
CLOCK_RE = re.compile(rf"\b({NUM})\s*-?\s*o'?\s*clock", re.I)
DIST_RE = re.compile(rf"\b({NUM})\s*(?:steps?|met(?:er|re)s?)\b", re.I)
AHEAD_RE = re.compile(r"\b(?:ahead|in front|front|straight)\b", re.I)
NEG_RE = re.compile(r"\b(?:no|without)\s+(?:\w+\s+){0,1}$", re.I)
CLEAR_RE = re.compile(
    r"unobstructed|is (?:clear|wide|open|flat|smooth)|road clear|clear and safe|no obstacles?|without worry|safe to pass|walk with ease",
    re.I,
)
MOVE_RE = re.compile(
    rf"\b(?:move|moving|walk|walking|go|going|head|heading|deviate|deviating|shift|turn|keep|keep moving|keep walking)\b(?:\s+(?:forward|slowly|straight|ahead|carefully|a|little|bit|the|road|on|it|by))*\s+(?:towards?|to|in|at)\s+(?:the\s+)?({NUM})\s*-?\s*o'?\s*clock",
    re.I,
)
OTHER_RE = re.compile(r"\bthere (?:is|are)\b|\bis an? \w+", re.I)
TURN_RE = re.compile(r"\bturn (left|right)\b", re.I)
STOP_RE = re.compile(
    r"(?<!who )\b(?:stop(?!\s*-?\s*(?:sign|point))|wait|give way|stand still|keep still)\b",
    re.I,
)
SLOW_RE = re.compile(r"\bslow\w*", re.I)
OPTIONS_RE = re.compile(
    r"\bcan (?:go|move|walk|turn)\b|\bone can\b", re.I
)  # "can go straight or turn left" = options, not an instruction
AVOID_TO_RE = re.compile(
    rf"\bavoid\w*\b[^.,;]{{0,30}}?\btowards?\s+(?:the\s+)?({NUM})\s*-?\s*o'?\s*clock",
    re.I,
)
CAT_RE = {c: re.compile(rf"\b(?:{p})\b", re.I) for c, p in CATEGORIES.items()}
num = lambda t: int(t) if t.isdigit() else NUMW[t.lower()]
valid_clock = lambda c: c if c is not None and 1 <= c <= 12 else None


def parse(text):
    t = str(text)
    # action (and remove the movement phrase so its clock isn't given to a hazard)
    action, action_clock = "continue", None
    m = MOVE_RE.search(t) or AVOID_TO_RE.search(t)
    if STOP_RE.search(t):
        action = "stop"
    elif m:
        action, action_clock = "move", valid_clock(num(m.group(1)))
    elif TURN_RE.search(t) and not OPTIONS_RE.search(t):
        action, action_clock = "move", (
            9 if TURN_RE.search(t).group(1).lower() == "left" else 3
        )
    elif SLOW_RE.search(t):
        action = "slow"
    t_h = AVOID_TO_RE.sub(" ", MOVE_RE.sub(" ", t))
    # hazards, clause by clause; each hazard takes the nearest direction cue in its clause
    hazards, pending_clock, pending_dist = [], None, None
    for clause in re.split(r"[,.;]| and (?=there|at|a |an )", t_h):
        cues = [
            (m.start(), valid_clock(num(m.group(1))))
            for m in CLOCK_RE.finditer(clause)
            if valid_clock(num(m.group(1)))
        ] + [(m.start(), 12) for m in AHEAD_RE.finditer(clause)]
        dists = [num(d) for d in DIST_RE.findall(clause)]
        found = []
        for cat, rx in CAT_RE.items():
            for mm in rx.finditer(clause):
                if NEG_RE.search(clause[: mm.start()]):
                    continue  # "no pedestrians"
                found.append((mm.start(), cat))
                break
        if not found and OTHER_RE.search(clause) and (cues or pending_clock):
            found = [
                (OTHER_RE.search(clause).start(), "other_object")
            ]  # unknown object with a direction
        if not found:  # "at 11 o'clock direction, there is ..."
            if (
                dists and hazards and hazards[-1]["dist_steps"] is None
            ):  # "... at 1 o'clock, 5 steps away"
                hazards[-1]["dist_steps"] = dists[0]
                continue
            pending_clock = (
                next((v for p, v in cues if v != 12), pending_clock)
                if cues
                else pending_clock
            )
            pending_dist = dists[0] if dists else pending_dist
            continue
        for pos, cat in sorted(found):
            clock = (
                min(cues, key=lambda c: abs(c[0] - pos))[1] if cues else pending_clock
            )
            hazards.append(
                dict(
                    category=cat,
                    clock=clock,
                    dist_steps=dists[0] if dists else pending_dist,
                )
            )
        pending_clock, pending_dist = None, None
    path_clear = bool(CLEAR_RE.search(t)) and not hazards
    first = hazards[0] if hazards else {}
    return dict(
        n_hazards=len(hazards),
        hazards="|".join(dict.fromkeys(h["category"] for h in hazards)),
        primary_hazard=first.get("category"),
        primary_clock=first.get("clock"),
        primary_dist_steps=first.get("dist_steps"),
        all_clocks="|".join(str(h["clock"]) for h in hazards if h["clock"]),
        action=action,
        action_clock=action_clock,
        path_clear=path_clear,
        parsed=bool(hazards) or path_clear,
    )
