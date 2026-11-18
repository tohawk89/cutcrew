"""The explainer character (flat vector starter design), recolourable per client.

Local units: origin = between the feet, y up is negative, facing right (3/4 view), ~740 units tall.
Use `Character(shirt=..., shirt_shadow=..., pants=..., pants_shadow=...)`, then:
  ch.svg(pose, face)                 plain SVG group (stills, character sheets)
  ch.person(id, pose, x, y, scale)   rig-ready group for animation: #id (move), #id-bob (bob),
                                     #id-eyes (blink), and with swap_to: #id-face1/#id-face2 + #id-arm
Poses: "stand", "keys", "point", "confused", "phone". Faces: "happy", "worried", "afraid", "down".
Hair: "A" side part (approved), "B" soft quiff, "C" short crop.
"""
import re

SHOULDER_N, SHOULDER_F = (84, -470), (-84, -470)
EYES_RE = re.compile(r'(<circle cx="4" cy="-6\d\d" r="7.5"[^>]*/><circle cx="42" cy="-6\d\d" r="7.5"[^>]*/>)')

HAIR_STYLES = {
    "A": "M-40,-604 L-38,-642 Q4,-648 40,-668 Q50,-650 52,-632 Q62,-640 68,-652 Q76,-700 24,-718 "
         "Q-30,-734 -66,-704 Q-86,-672 -80,-624 Q-78,-596 -68,-580 L-60,-600 Q-54,-614 -40,-604 Z",
    "B": "M-40,-604 L-38,-640 Q0,-650 30,-642 L44,-626 L50,-652 Q62,-656 68,-664 L86,-688 "
         "Q72,-702 56,-708 L62,-732 Q38,-722 20,-726 L10,-744 Q-16,-730 -46,-724 "
         "Q-84,-700 -80,-628 Q-78,-598 -68,-580 L-60,-600 Q-54,-614 -40,-604 Z",
    "C": "M-40,-604 L-38,-640 Q12,-654 64,-644 Q74,-704 0,-712 Q-74,-710 -80,-630 "
         "Q-78,-598 -68,-580 L-60,-600 Q-54,-614 -40,-604 Z",
}


class Character:
    def __init__(self, shirt="#3FC1AE", shirt_shadow="#30A492", pants="#2F2A5B", pants_shadow="#24204A",
                 skin="#F4A07F", skin_shadow="#DE8467", hair="#2A2D3E", hair_style="A",
                 shoe="#1E1A3A", sole="#5B567F", collar="#ECEAF3", mouth="#6B2232",
                 accent="#F2B630", problem="#F08C3A", phone="#2F2A5B"):
        self.c = dict(shirt=shirt, shirt_sh=shirt_shadow, pants=pants, pants_sh=pants_shadow, skin=skin,
                      skin_sh=skin_shadow, hair=hair, shoe=shoe, sole=sole, collar=collar, mouth=mouth,
                      accent=accent, problem=problem, phone=phone)
        self.hair_d = HAIR_STYLES.get(hair_style, hair_style)

    # ---- parts ----
    def limb(self, p0, p1, p2, color=None, w_up=40, w_fore=33):
        """Upper arm + forearm as round-capped strokes with an elbow joint circle (tapered, rig-friendly)."""
        color = color or self.c["shirt"]
        (x0, y0), (x1, y1), (x2, y2) = p0, p1, p2
        return (f'<path d="M{x0},{y0} L{x1},{y1}" stroke="{color}" stroke-width="{w_up}" stroke-linecap="round"/>'
                f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="{w_fore}" stroke-linecap="round"/>'
                f'<circle cx="{x1}" cy="{y1}" r="{w_fore/2+1}" fill="{color}"/>')

    def hand_relaxed(self, x, y, rot=0, skin=None):
        sk = skin or self.c["skin"]
        return (f'<g transform="translate({x},{y}) rotate({rot})">'
                f'<path d="M-15,-4 L15,-4 Q20,24 11,38 Q0,47 -11,38 Q-20,24 -15,-4 Z" fill="{sk}"/>'
                f'<path d="M12,2 Q27,8 24,24 Q17,28 11,20 Z" fill="{sk}"/></g>')

    def hand_point(self, x, y, rot=0):
        sk, sh = self.c["skin"], self.c["skin_sh"]
        return (f'<g transform="translate({x},{y}) rotate({rot})">'
                f'<rect x="-6" y="-16" width="36" height="32" rx="13" fill="{sk}"/>'
                f'<rect x="22" y="-16" width="36" height="12" rx="6" fill="{sk}"/>'
                f'<path d="M4,-14 Q16,-26 28,-18 Q22,-10 10,-8 Z" fill="{sh}"/></g>')

    def hand_open(self, x, y, rot=0):
        sk = self.c["skin"]
        return (f'<g transform="translate({x},{y}) rotate({rot})">'
                f'<rect x="-15" y="-6" width="30" height="36" rx="12" fill="{sk}"/>'
                f'<rect x="-14" y="20" width="9" height="22" rx="4.5" fill="{sk}"/>'
                f'<rect x="-4" y="22" width="9" height="24" rx="4.5" fill="{sk}"/>'
                f'<rect x="6" y="20" width="9" height="21" rx="4.5" fill="{sk}"/>'
                f'<path d="M13,0 Q28,4 26,18 Q19,20 13,12 Z" fill="{sk}"/></g>')

    def fist_front(self, x, y, rot=0):
        sk, sh = self.c["skin"], self.c["skin_sh"]
        return (f'<g transform="translate({x},{y}) rotate({rot})">'
                f'<rect x="-17" y="-14" width="34" height="30" rx="12" fill="{sk}"/>'
                f'<path d="M-17,-2 L17,-2 M-17,8 L17,8" stroke="{sh}" stroke-width="2.5"/>'
                f'<ellipse cx="-14" cy="-14" rx="9" ry="7" fill="{sk}"/></g>')

    def legs(self):
        c = self.c
        return (f'<path d="M-64,-282 L-16,-282 L-20,-26 L-56,-26 Z" fill="{c["pants_sh"]}"/>'
                f'<path d="M14,-282 L64,-282 L58,-26 L22,-26 Z" fill="{c["pants"]}"/>'
                f'<path d="M-62,0 L-62,-20 Q-62,-36 -44,-36 L-24,-36 Q-2,-34 4,-12 L4,0 Z" fill="{c["shoe"]}"/>'
                f'<rect x="-62" y="-7" width="66" height="7" rx="3" fill="{c["sole"]}"/>'
                f'<path d="M16,0 L16,-20 Q16,-36 34,-36 L54,-36 Q78,-34 84,-12 L84,0 Z" fill="{c["shoe"]}"/>'
                f'<rect x="16" y="-7" width="68" height="7" rx="3" fill="{c["sole"]}"/>')

    def torso(self):
        c = self.c
        return (f'<path d="M-40,-504 C-82,-504 -106,-494 -108,-458 L-80,-290 Q-78,-276 -64,-276 L64,-276 '
                f'Q78,-276 80,-290 L108,-458 C106,-494 82,-504 40,-504 Z" fill="{c["shirt"]}"/>'
                f'<path d="M-108,-458 L-80,-290 Q-78,-276 -64,-276 L-62,-276 L-92,-454 Z" fill="{c["shirt_sh"]}"/>')

    def neck(self):
        c = self.c
        return (f'<rect x="-21" y="-552" width="42" height="56" fill="{c["skin"]}"/>'
                f'<rect x="-21" y="-552" width="42" height="18" fill="{c["skin_sh"]}"/>'
                f'<path d="M-36,-503 Q0,-470 36,-503 L28,-511 Q0,-488 -28,-511 Z" fill="{c["collar"]}"/>')

    def head(self):
        c = self.c
        return (f'<path d="M28,-530 Q58,-530 62,-562 L64,-622 C64,-690 -62,-700 -66,-622 L-62,-586 '
                f'Q-58,-552 -22,-536 Q0,-528 28,-530 Z" fill="{c["skin"]}"/>'
                f'<path d="{self.hair_d}" fill="{c["hair"]}"/>'
                f'<ellipse cx="-50" cy="-596" rx="16" ry="24" fill="{c["skin"]}"/>'
                f'<path d="M-46,-608 Q-56,-596 -47,-583" stroke="{c["skin_sh"]}" stroke-width="6" fill="none" stroke-linecap="round"/>')

    def face(self, name):
        h, m = self.c["hair"], self.c["mouth"]
        return {
            "happy": (f'<circle cx="4" cy="-608" r="7.5" fill="{h}"/><circle cx="42" cy="-608" r="7.5" fill="{h}"/>'
                      f'<path d="M-2,-578 L48,-578 Q46,-546 23,-546 Q0,-548 -2,-578 Z" fill="{m}"/>'
                      f'<path d="M0,-578 L46,-578 L45,-570 L1,-570 Z" fill="#FFFFFF"/>'
                      f'<ellipse cx="23" cy="-552" rx="11" ry="4.5" fill="#E8707D"/>'),
            "worried": (f'<circle cx="4" cy="-606" r="7.5" fill="{h}"/><circle cx="42" cy="-606" r="7.5" fill="{h}"/>'
                        f'<path d="M-8,-624 L12,-632 M34,-632 L54,-624" stroke="{h}" stroke-width="5" stroke-linecap="round"/>'
                        f'<path d="M10,-562 Q24,-572 38,-562" stroke="{m}" stroke-width="7" fill="none" stroke-linecap="round"/>'),
            "afraid": ('<ellipse cx="4" cy="-608" rx="13" ry="15" fill="#FFFFFF"/><ellipse cx="44" cy="-608" rx="13" ry="15" fill="#FFFFFF"/>'
                       f'<circle cx="6" cy="-606" r="6" fill="{h}"/><circle cx="46" cy="-606" r="6" fill="{h}"/>'
                       f'<path d="M-12,-632 Q2,-646 18,-638 M30,-638 Q46,-646 60,-632" stroke="{h}" stroke-width="5" fill="none" stroke-linecap="round"/>'
                       f'<ellipse cx="25" cy="-560" rx="9" ry="12" fill="{m}"/>'
                       '<path d="M66,-650 q-9,14 0,20 q9,-6 0,-20 Z" fill="#9ED3E4"/>'),
            "down": (f'<path d="M-4,-600 Q4,-594 12,-600 M34,-600 Q42,-594 50,-600" stroke="{h}" stroke-width="5" fill="none" stroke-linecap="round"/>'
                     f'<path d="M6,-572 L40,-572 Q38,-556 23,-556 Q8,-556 6,-572 Z" fill="{m}"/>'
                     f'<path d="M7,-572 L39,-572 L38,-567 L8,-567 Z" fill="#FFFFFF"/>'),
        }[name]

    def far_arm(self):
        return self.limb(SHOULDER_F, (-104, -384), (-98, -308), color=self.c["shirt_sh"]) + \
            self.hand_relaxed(-98, -304, 6, self.c["skin_sh"])

    def front_arm(self, pose):
        c = self.c
        if pose == "keys":
            return (self.limb(SHOULDER_N, (140, -404), (150, -486))
                    + f'<circle cx="158" cy="-534" r="14" fill="none" stroke="{c["accent"]}" stroke-width="6"/>'
                    + f'<rect x="164" y="-566" width="11" height="32" rx="4" fill="{c["accent"]}" transform="rotate(20 170 -550)"/>'
                    + self.fist_front(152, -502, -10))
        if pose == "point":
            return self.limb(SHOULDER_N, (150, -440), (214, -462)) + self.hand_point(222, -464, -8)
        if pose == "confused":
            return self.limb(SHOULDER_N, (150, -548), (60, -662)) + self.hand_open(40, -688, 200)
        if pose == "phone":
            return (self.limb(SHOULDER_N, (114, -372), (70, -424))
                    + f'<g transform="rotate(-12 58 -470)"><rect x="28" y="-528" width="60" height="106" rx="11" fill="{c["phone"]}"/>'
                    + '<rect x="34" y="-519" width="48" height="86" rx="6" fill="#E6F7F3"/>'
                    + f'<rect x="40" y="-452" width="36" height="12" rx="6" fill="{c["shirt"]}"/></g>'
                    + self.fist_front(58, -432, -12))
        # stand
        return self.limb(SHOULDER_N, (104, -384), (98, -308)) + self.hand_relaxed(98, -304, -6)

    DEFAULT_FACE = {"keys": "happy", "point": "happy", "confused": "worried", "phone": "down", "stand": "happy"}

    # ---- whole character ----
    def svg(self, pose="stand", face=None):
        f = face or self.DEFAULT_FACE[pose]
        s = self.legs() + self.far_arm() + self.torso() + self.neck() + self.head() + self.face(f) + self.front_arm(pose)
        if pose == "confused":
            s += (f'<circle cx="160" cy="-770" r="46" fill="#FFFFFF"/>'
                  f'<text x="160" y="-749" text-anchor="middle" class="t" font-size="60" style="fill:{self.c["problem"]}">?</text>')
        return s

    def person(self, id_, pose, x, y, scale=1.0, face=None, swap_to=None):
        """Rig-ready: #id (slide), #id-bob (bob/sway), #id-eyes (blink); swap_to adds #id-face1/-face2 and #id-arm."""
        f = face or self.DEFAULT_FACE[pose]
        body = self.legs() + self.far_arm() + self.torso() + self.neck() + self.head()
        arm = self.front_arm(pose)
        if swap_to:
            c = (body + f'<g id="{id_}-face1">{self.face(f)}</g>'
                 + f'<g id="{id_}-face2" opacity="0">{self.face(swap_to)}</g>' + f'<g id="{id_}-arm">{arm}</g>')
        else:
            c = body + self.face(f) + arm
        if pose == "confused":
            c += (f'<g id="{id_}-q"><circle cx="160" cy="-770" r="46" fill="#FFFFFF"/>'
                  f'<text x="160" y="-749" text-anchor="middle" class="t" font-size="60" style="fill:{self.c["problem"]}">?</text></g>')
        c = EYES_RE.sub(rf'<g id="{id_}-eyes">\1</g>', c, count=1)
        return f'<g transform="translate({x},{y}) scale({scale})"><g id="{id_}"><g id="{id_}-bob">{c}</g></g></g>'


# Shoulder of the front arm, in character units: the pivot for arm moves (svgOrigin "84 -470").
ARM_PIVOT = "84 -470"
