"""Seed a NEW TACTIC project from TACTIC Handler's Server Python editor.

Set PROJECT_CODE and the switches below. Run repeatedly, as an administrator, until the
returned phase is "complete". Each run commits a short portion of the work.
After a timeout, wait for the server request to finish, then set INSPECT_ONLY
to True and run once to read counts before continuing. Existing demo objects
are reused; later runs add tags and parent-visible discussions. The script
does not create search types or change
the schema. Every note is marked DEMO. Demo logins and groups are global to
TACTIC; new logins get random passwords that an admin must reset before use.
"""

PROJECT_CODE = "SET_PROJECT_CODE"

CATEGORY_TYPE = "complex/assets_category"
EPISODE_TYPE = "complex/scenes"
SHOT_TYPE = "complex/shot"
ASSET_TYPE = "dolly3d/assets"
TEXTURE_TYPE = "dolly3d/texture"

import random
import re
import secrets
import time


EPISODES = 500
ASSETS = 4000
TEXTURES = 4000
USERS = 200
SEED = 20260922
MAX_SECONDS_PER_RUN = 20
INSPECT_ONLY = False

# Turn off any section you do not want. Links and notes need their parent
# objects; the script reports a missing dependency instead of creating it.
CREATE_USERS = True
CREATE_GROUPS = True
CREATE_EPISODES = True
CREATE_SHOTS = True
CREATE_EPISODE_TASKS = True
CREATE_EPISODE_TASK_NOTES = True
CREATE_EPISODE_NOTES = True
CREATE_CATEGORIES = True
CREATE_ASSETS = True
LINK_EPISODE_ASSETS = True
CREATE_TEXTURES = True
LINK_ASSET_TEXTURES = True
TAG_EPISODES = True
TAG_ASSETS = True
CREATE_ASSET_TASKS = True
CREATE_ASSET_NOTES = True

DEMO_LOGIN_PREFIX = "demo_user_"
DEMO_GROUPS = (
    "demo_story", "demo_layout", "demo_model", "demo_rig",
    "demo_texture", "demo_animation", "demo_fx", "demo_lighting",
    "demo_render", "demo_compositing", "demo_editorial", "demo_production",
)
FIRST_NAMES = (
    "Alex", "Morgan", "Taylor", "Jordan", "Casey", "Riley", "Avery",
    "Jamie", "Robin", "Cameron", "Drew", "Quinn", "Skyler", "Reese",
    "Parker", "Blake", "Charlie", "Sam", "Harper", "Bailey",
)
LAST_NAMES = (
    "Miller", "Chen", "Rivera", "Patel", "Garcia", "Kim", "Brown",
    "Lee", "Walker", "Nguyen",
)

EPISODE_TITLES = (
    "A New Beginning", "The Missing Map", "Morning at the Harbor",
    "The Hidden Room", "A Strange Visitor", "Across the Bridge",
    "The Last Train", "Night in the City", "The Secret Signal",
    "The Long Way Home", "An Unexpected Friend", "The Great Escape",
    "A Day of Discoveries", "The Storm Arrives", "The Quiet Forest",
    "The Final Clue", "After the Rain", "The Workshop Mystery",
    "The Festival", "A Promise Kept", "The Broken Compass",
    "The First Flight", "Under the Old Bridge", "The Lighthouse Keeper",
    "An Invitation at Midnight", "The Forgotten Garden", "The Blue Door",
    "The Mountain Path", "A Message in a Bottle", "The Clockwork Bird",
    "The Other Side", "The Painted Window", "The Lost Package",
    "The River Crossing", "The Curious Machine", "A Place to Hide",
    "The Unexpected Detour", "The Empty Station", "The Secret Workshop",
    "The Journey Begins",
)
EPISODE_SETTINGS = (
    "The Old Harbor", "North Island", "Market Square", "The Observatory",
    "The Glasshouse", "The Railway Yard", "Cloud Valley", "The Museum",
    "The Hidden Alley", "The Mountain Camp", "The Riverside", "The Clock Tower",
    "The Sunken Pier", "The Great Library", "The City Rooftops",
)
CATEGORIES = {
    "Character": ("Explorer", "Pilot", "Captain", "Scientist", "Merchant", "Guardian", "Mechanic", "Courier", "Inventor", "Navigator"),
    "Creature": ("Fox", "Raven", "Otter", "Dragon", "Robot", "Moth", "Owl", "Hedgehog", "Salamander", "Whale"),
    "Prop": ("Compass", "Lantern", "Notebook", "Crate", "Radio", "Key", "Telescope", "Map", "Music Box", "Pocket Watch"),
    "Environment": ("Harbor", "Forest", "Station", "Courtyard", "Workshop", "Market", "Canyon", "Greenhouse", "Cave", "Rooftop"),
    "Vehicle": ("Bicycle", "Airship", "Train", "Boat", "Truck", "Glider", "Submarine", "Tram", "Scooter", "Balloon"),
    "Wardrobe": ("Jacket", "Hat", "Boots", "Cape", "Uniform", "Backpack", "Scarf", "Gloves", "Coat", "Goggles"),
    "Architecture": ("Tower", "Bridge", "House", "Gate", "Platform", "Lighthouse", "Observatory", "Warehouse", "Arcade", "Pier"),
    "Equipment": ("Camera", "Drone", "Projector", "Scanner", "Microphone", "Tablet", "Beacon", "Generator", "Monitor", "Transmitter"),
    "Furniture": ("Desk", "Chair", "Cabinet", "Bookshelf", "Bench", "Workbench", "Lamp", "Sofa", "Stool", "Counter"),
    "Set Dressing": ("Poster", "Sign", "Plant", "Suitcase", "Barrel", "Rope", "Bottle", "Banner", "Clock", "Basket"),
}
ASSET_VARIANTS = (
    "Old", "New", "Painted", "Weathered", "Small", "Large", "Copper",
    "Wooden", "Blue", "Red", "Striped", "Travel", "Festival", "Workshop",
    "Prototype", "Damaged", "Restored", "Night", "Garden", "Harbor",
)
TEXTURE_KINDS = (
    "Diffuse", "Base Color", "Normal", "Displacement", "Height",
    "Roughness", "Metalness", "Emissive", "Opacity", "AO",
    "Specular", "Bump", "Mask", "Subsurface",
)
TASK_TEXTS = (
    "Prepare references and check the brief",
    "Build the first layout pass",
    "Review shot continuity and timing",
    "Create the initial design pass",
    "Update the scene after director feedback",
    "Check materials and lighting",
    "Polish the animation and transitions",
    "Fix issues found during internal review",
    "Prepare assets for the next department",
    "Verify the latest render and color balance",
    "Collect notes from the team",
    "Approve the final version for handoff",
    "Check naming and published files",
    "Resolve remaining technical warnings",
    "Prepare the preview for review",
    "Confirm delivery and archive the source files",
)
NOTE_VARIANTS = (
    ("I have started the task and checked the brief.",
     "I am taking this one; the source files look good.",
     "Starting the first pass now. I will share a preview shortly.",
     "I picked this up and gathered the latest references."),
    ("Could you review the first pass when you have a moment?",
     "The initial version is ready for a quick look.",
     "I have uploaded a preview. Please let me know what you think.",
     "Ready for review; the main shapes and timing are in place."),
    ("The overall direction works, but the details need another pass.",
     "Nice progress. Please adjust the scale in the final section.",
     "The composition reads well. Can we improve the transition?",
     "Please compare this against the latest reference before continuing."),
    ("Thanks, I have applied the requested changes.",
     "I updated the scene and posted a new preview.",
     "The scale and timing are corrected in the latest version.",
     "Revised version is ready; please check it again."),
    ("I checked the update. The main issue is resolved.",
     "This looks much closer. One small detail remains.",
     "The new preview matches the reference on my side.",
     "Good improvement. Please confirm the final frame."),
    ("Final check is complete; no further changes from me.",
     "Looks good. We can move this to the next stage.",
     "Approved for the demo handoff.",
     "I am happy with this version. Thanks for the quick turnaround."),
    ("I have also checked the exported files and naming.",
     "The preview and source files are now in sync.",
     "One final render is queued for the team.",
     "I added a short handoff note for the next department."),
    ("Thanks, I will keep an eye on any follow-up notes.",
     "Received. I will pick it up if anything else changes.",
     "Great, the handoff is complete on my side.",
     "All set. Let us know if another pass is needed."),
)
EPISODE_TAGS = (
    "adventure", "mystery", "comedy", "drama", "action", "quiet",
    "night", "day", "interior", "exterior", "flashback", "chase",
    "dialogue", "travel", "discovery", "storm", "festival", "forest",
    "harbor", "city", "mountain", "workshop", "review", "finale",
)
ASSET_TAGS = (
    "hero", "background", "featured", "crowd", "stylized", "realistic",
    "small", "large", "new", "weathered", "painted", "wood", "metal",
    "fabric", "glass", "stone", "organic", "mechanical", "day",
    "night", "interior", "exterior", "interactive", "animated",
    "prototype", "approved", "high-detail", "low-poly", "set-dressing",
)
ASSET_DISCUSSION_DONE = "[DEMO] Asset tasks and review notes are ready for handoff."
EPISODE_DISCUSSION_DONE = "[DEMO] Episode review notes are ready for handoff."


def batches(items, size=100):
    for start in range(0, len(items), size):
        yield items[start:start + size]


def records(search_type, data, parent_key=None):
    """Use native TACTIC batch insert and reject incomplete responses."""
    result = server.insert_multiple(
        search_type, data, parent_key=parent_key, triggers=False
    )
    if len(result or ()) != len(data) or any(
        not row.get("__search_key__") for row in result
    ):
        raise RuntimeError("Incomplete insert_multiple result for %s" % search_type)
    return result


def available_type(search_type):
    from pyasm.search import SearchType

    columns = set(SearchType.get_columns(search_type) or ())
    if not {"code", "name"} <= columns:
        raise RuntimeError("Missing code/name columns on %s" % search_type)
    return columns


def fields(columns, code, name, description, **optional):
    result = {"code": code, "name": name}
    if "description" in columns:
        result["description"] = description
    result.update({key: value for key, value in optional.items() if key in columns})
    return result


def add_tags(item, column, tags):
    current = str(item.get_value(column) or "")
    existing = {part.casefold() for part in re.split(r"[,;\s]+", current) if part}
    missing = []
    for tag in tags:
        if tag.casefold() not in existing:
            missing.append(tag)
            existing.add(tag.casefold())
    if not missing:
        return False
    item.set_value(column, (current.rstrip(",; ") + ", " if current.strip() else "")
                   + ", ".join(missing))
    item.commit(triggers=False)
    return True


def seed_project():
    from pyasm.biz import Schema
    from pyasm.search import Search, SearchKey, SearchType

    if not PROJECT_CODE or PROJECT_CODE == "SET_PROJECT_CODE":
        raise RuntimeError("Set PROJECT_CODE at the top of the script first")

    project_search = Search("sthpw/project")
    project_search.add_filter("code", PROJECT_CODE)
    if not project_search.get_sobject():
        raise RuntimeError("Project %s does not exist" % PROJECT_CODE)
    server.set_project(PROJECT_CODE)

    schema = Schema.get(project_code=PROJECT_CODE)

    login_search = Search("sthpw/login")
    login_search.set_show_retired(True)
    login_objects = {
        str(item.get_value("login")): item
        for item in login_search.get_sobjects() if item.get_value("login")
    }
    demo_logins = {name for name in login_objects if name.startswith(DEMO_LOGIN_PREFIX)}
    existing_team = {
        name for name in login_objects
        if name != "guest" and not name.startswith(DEMO_LOGIN_PREFIX)
    }
    # An existing two-person team is enough for task conversations. Never
    # inject 200 global logins into an already staffed TACTIC server.
    seed_demo_team = bool(demo_logins) or (CREATE_USERS and len(existing_team) < 2)

    def demo_group_count():
        return sum(
            item.get_value("login_group") in DEMO_GROUPS
            for item in Search("sthpw/login_group").get_sobjects()
        )

    def discussion_count(parent_type, marker):
        search = Search("sthpw/note")
        search.add_filter("project_code", PROJECT_CODE)
        search.add_filter("search_type", parent_type + "%", op="like")
        search.add_filter("note", marker)
        return search.get_count()

    if INSPECT_ONLY:
        episode_asset_type = (schema.get_relationship_attrs(EPISODE_TYPE, ASSET_TYPE) or {}).get("instance_type")
        asset_texture_type = (schema.get_relationship_attrs(ASSET_TYPE, TEXTURE_TYPE) or {}).get("instance_type")
        return {
            "project": PROJECT_CODE,
            "phase": "inspection",
            "counts": {
                "users": len(demo_logins),
                "groups": demo_group_count(),
                "categories": Search(CATEGORY_TYPE).get_count(),
                "episodes": Search(EPISODE_TYPE).get_count(),
                "shots": Search(SHOT_TYPE).get_count(),
                "assets": Search(ASSET_TYPE).get_count(),
                "episode_asset_links": Search(episode_asset_type).get_count() if episode_asset_type else None,
                "textures": Search(TEXTURE_TYPE).get_count(),
                "asset_texture_links": Search(asset_texture_type).get_count() if asset_texture_type else None,
                "episode_discussions": discussion_count(
                    EPISODE_TYPE, EPISODE_DISCUSSION_DONE),
                "asset_discussions": discussion_count(
                    ASSET_TYPE, ASSET_DISCUSSION_DONE),
            },
        }

    category_columns = available_type(CATEGORY_TYPE) if CREATE_CATEGORIES else set()
    episode_columns = available_type(EPISODE_TYPE) if CREATE_EPISODES or TAG_EPISODES else set()
    shot_columns = available_type(SHOT_TYPE) if CREATE_SHOTS else set()
    asset_columns = available_type(ASSET_TYPE) if CREATE_ASSETS or TAG_ASSETS else set()
    texture_columns = available_type(TEXTURE_TYPE) if CREATE_TEXTURES else set()
    if CREATE_SHOTS:
        children = set(schema.get_related_search_types(EPISODE_TYPE, direction="children") or ())
        if SHOT_TYPE not in children:
            raise RuntimeError("Configure the Episode -> Shot child relation before seeding")

    category_relation = (dict(schema.get_relationship_attrs(ASSET_TYPE, CATEGORY_TYPE) or {})
                         if CREATE_ASSETS else {})
    category_column = category_relation.get("from_col")
    if (CREATE_ASSETS and (category_relation.get("relationship") != "code"
            or category_relation.get("from") != ASSET_TYPE
            or category_relation.get("to") != CATEGORY_TYPE
            or category_column not in asset_columns)):
        raise RuntimeError("Configure the Asset -> Category code relation before seeding")

    episode_asset = (dict(schema.get_relationship_attrs(EPISODE_TYPE, ASSET_TYPE) or {})
                     if LINK_EPISODE_ASSETS else {})
    asset_texture = (dict(schema.get_relationship_attrs(ASSET_TYPE, TEXTURE_TYPE) or {})
                     if LINK_ASSET_TEXTURES else {})
    for relation, first, second in (
            (episode_asset, EPISODE_TYPE, ASSET_TYPE),
            (asset_texture, ASSET_TYPE, TEXTURE_TYPE)):
        if not relation:
            continue
        if (relation.get("relationship") != "instance"
                or not relation.get("instance_type")
                or {relation.get("from"), relation.get("to")} != {first, second}):
            raise RuntimeError("Configure the %s -> %s instance relation before seeding" % (first, second))

    def count(search_type):
        return Search(search_type).get_count()

    def key(search_type, code):
        return SearchKey.build_search_key(search_type, code, project_code=PROJECT_CODE)

    def sobject(search_type, code):
        item = SearchKey.get_by_search_key(key(search_type, code))
        if item is None:
            raise RuntimeError("Missing %s code %s" % (search_type, code))
        return item

    def link(relation, first_type, first, second):
        instance = SearchType.create(relation["instance_type"])
        if relation["from"] == first_type:
            instance.add_related_connection(first, second, src_path=relation.get("path"))
        else:
            instance.add_related_connection(second, first, src_path=relation.get("path"))
        instance.commit()

    def report(phase, processed=0):
        return {
            "project": PROJECT_CODE,
            "phase": phase,
            "processed_this_run": processed,
            "run_again": phase != "complete",
            "counts": {
                "users": len(demo_logins),
                "groups": demo_group_count(),
                "categories": count(CATEGORY_TYPE),
                "episodes": count(EPISODE_TYPE),
                "shots": count(SHOT_TYPE),
                "assets": count(ASSET_TYPE),
                "episode_asset_links": (count(episode_asset["instance_type"])
                                        if episode_asset else None),
                "textures": count(TEXTURE_TYPE),
                "asset_texture_links": (count(asset_texture["instance_type"])
                                        if asset_texture else None),
            },
        }

    started = time.time()
    if seed_demo_team and CREATE_GROUPS:
        existing_groups = {
            str(item.get_value("login_group"))
            for item in Search("sthpw/login_group").get_sobjects()
        }
        created = 0
        for name in DEMO_GROUPS:
            if name in existing_groups:
                continue
            group = SearchType.create("sthpw/login_group")
            group.set_value("login_group", name)
            group.set_value("description", "Demo production team: " + name[5:])
            group.commit()
            created += 1
            if time.time() - started >= MAX_SECONDS_PER_RUN:
                break
        if created:
            return report("groups_created", created)

    if seed_demo_team and CREATE_USERS:
        from pyasm.security import Login

        created = 0
        for index in range(1, USERS + 1):
            name = "%s%03d" % (DEMO_LOGIN_PREFIX, index)
            if name in login_objects:
                continue
            first = FIRST_NAMES[(index - 1) % len(FIRST_NAMES)]
            last = LAST_NAMES[(index - 1) // len(FIRST_NAMES) % len(LAST_NAMES)]
            groups = ([DEMO_GROUPS[(index - 1) % len(DEMO_GROUPS)]]
                      if CREATE_GROUPS else [])
            user = Login.create(
                name, secrets.token_urlsafe(24), groups=groups,
                project_code=PROJECT_CODE,
            )
            user.set_value("first_name", first)
            user.set_value("last_name", last)
            user.set_value("display_name", first + " " + last)
            user.commit()
            login_objects[name] = user
            demo_logins.add(name)
            created += 1
            if time.time() - started >= MAX_SECONDS_PER_RUN:
                break
        if created:
            return report("users_created", created)

    if seed_demo_team and CREATE_GROUPS and demo_logins:
        memberships = {
            (str(item.get_value("login")), str(item.get_value("login_group")))
            for item in Search("sthpw/login_in_group").get_sobjects()
        }
        assigned = 0
        for index in range(1, USERS + 1):
            name = "%s%03d" % (DEMO_LOGIN_PREFIX, index)
            if name not in demo_logins:
                continue
            group = DEMO_GROUPS[(index - 1) % len(DEMO_GROUPS)]
            if (name, group) in memberships:
                continue
            login_objects[name].add_to_group(group)
            assigned += 1
            if time.time() - started >= MAX_SECONDS_PER_RUN:
                break
        if assigned:
            return report("memberships_created", assigned)

    episode_count = count(EPISODE_TYPE)
    if episode_count == 0 and CREATE_EPISODES:
        episode_rows = [
            fields(episode_columns, "DEMO_EP%03d" % index,
                   "Episode %03d — %s: %s" % (
                       index,
                       EPISODE_TITLES[(index - 1) % len(EPISODE_TITLES)],
                       EPISODE_SETTINGS[(index - 1) // len(EPISODE_TITLES) % len(EPISODE_SETTINGS)],
                   ),
                   "Synthetic episode for interface demonstrations")
            for index in range(1, EPISODES + 1)
        ]
        for batch in batches(episode_rows):
            records(EPISODE_TYPE, batch)
        return report("episodes_created", EPISODES)
    if episode_count != EPISODES and (CREATE_SHOTS or CREATE_EPISODE_TASKS
            or CREATE_EPISODE_TASK_NOTES or CREATE_EPISODE_NOTES
            or TAG_EPISODES or LINK_EPISODE_ASSETS):
        raise RuntimeError("Expected %d episodes, found %d; inspect before continuing" % (EPISODES, episode_count))

    shot_total = count(SHOT_TYPE)
    asset_count = count(ASSET_TYPE)
    texture_count = count(TEXTURE_TYPE)
    if CREATE_SHOTS:
        shot_prefix = [0]
        for index in range(1, EPISODES + 1):
            shot_prefix.append(shot_prefix[-1] + random.Random(SEED + index).randint(2, 20))
        if shot_total not in shot_prefix:
            raise RuntimeError("Shot count %d does not match a completed episode batch" % shot_total)
        completed_episodes = shot_prefix.index(shot_total)
        if completed_episodes < EPISODES:
            processed = 0
            for episode_index in range(completed_episodes + 1, EPISODES + 1):
                rng = random.Random(SEED + episode_index)
                episode_key = key(EPISODE_TYPE, "DEMO_EP%03d" % episode_index)
                shot_rows = [
                    fields(shot_columns, "DEMO_EP%03d_SH%03d" % (episode_index, shot_index),
                           "SH%03d" % (shot_index * 10),
                           "Episode %03d, shot %03d" % (episode_index, shot_index * 10))
                    for shot_index in range(1, rng.randint(2, 20) + 1)
                ]
                records(SHOT_TYPE, shot_rows, parent_key=episode_key)
                processed += len(shot_rows)
                if time.time() - started >= MAX_SECONDS_PER_RUN:
                    break
            return report("shots_created", processed)

    if CREATE_EPISODE_TASKS or CREATE_EPISODE_TASK_NOTES:
        logins = sorted(name for name in login_objects if name != "guest")
        if len(logins) < 2:
            raise RuntimeError("At least two TACTIC users are needed for demo tasks and notes")
        pipeline_search = Search("sthpw/pipeline")
        pipeline_search.add_filter("search_type", EPISODE_TYPE)
        pipeline_search.add_filter("project_code", PROJECT_CODE)
        pipelines = pipeline_search.get_sobjects()
        processes = list(pipelines[0].get_process_names()) if pipelines else []
        if not processes:
            raise RuntimeError("Configure an Episode pipeline with processes before seeding tasks")
        episode_search = Search(EPISODE_TYPE)
        episode_search.add_filter("code", "DEMO_EP%", op="like")
        existing_tasks = set()
        existing_notes = set()
        if CREATE_EPISODE_TASKS or CREATE_EPISODE_TASK_NOTES:
            task_search = Search("sthpw/task")
            task_search.add_filter("project_code", PROJECT_CODE)
            task_search.add_filter("search_type", EPISODE_TYPE + "%", op="like")
            existing_tasks = {
                (item.get_value("search_id"), item.get_value("process"), item.get_value("description"))
                for item in task_search.get_sobjects()
            }
        if CREATE_EPISODE_TASK_NOTES:
            note_search = Search("sthpw/note")
            note_search.add_filter("project_code", PROJECT_CODE)
            note_search.add_filter("search_type", EPISODE_TYPE + "%", op="like")
            existing_notes = {
                (item.get_value("search_id"), item.get_value("process"), item.get_value("note"))
                for item in note_search.get_sobjects()
            }
        processed = 0
        for episode in sorted(episode_search.get_sobjects(), key=lambda item: item.get_value("code")):
            code = str(episode.get_value("code"))
            suffix = code[len("DEMO_EP"):]
            if not suffix.isdigit() or not 1 <= int(suffix) <= EPISODES:
                continue
            episode_index = int(suffix)
            rng = random.Random(SEED + episode_index)
            rng.randint(2, 20)  # Keep task/note choices independent of the shot switch.
            episode_key = key(EPISODE_TYPE, "DEMO_EP%03d" % episode_index)
            selected_processes = [processes[(episode_index + offset) % len(processes)] for offset in range(4)]
            task_descriptions = rng.sample(TASK_TEXTS, 4)
            task_rows = [
                {"process": process, "assigned": rng.choice(logins),
                 "description": task_descriptions[index]}
                for index, process in enumerate(selected_processes)
            ]
            changed = False
            if CREATE_EPISODE_TASKS:
                missing = [row for row in task_rows
                           if (episode.get_id(), row["process"], row["description"])
                           not in existing_tasks]
                if missing:
                    records("sthpw/task", missing, parent_key=episode_key)
                    existing_tasks.update(
                        (episode.get_id(), row["process"], row["description"])
                        for row in missing
                    )
                    changed = True
            if (CREATE_EPISODE_TASK_NOTES and not any(
                    identity[0] == episode.get_id()
                    and identity[2] == EPISODE_DISCUSSION_DONE
                    for identity in existing_notes)):
                if not any(identity[0] == episode.get_id() for identity in existing_tasks):
                    raise RuntimeError("Episode %s needs tasks before notes" % code)
                note_rows = []
                for task_row in task_rows:
                    process = task_row["process"]
                    participants = rng.sample(logins, 2)
                    for position in range(rng.randint(4, 8)):
                        text = "[DEMO] " + rng.choice(NOTE_VARIANTS[position])
                        identity = (episode.get_id(), process, text)
                        if identity not in existing_notes:
                            note_rows.append({
                                "process": process, "context": process,
                                "login": participants[position % 2], "note": text,
                            })
                            existing_notes.add(identity)
                if note_rows:
                    records("sthpw/note", note_rows, parent_key=episode_key)
                    changed = True
            if changed:
                processed += 1
            if processed and time.time() - started >= MAX_SECONDS_PER_RUN:
                break
        if processed:
            return report("episode_tasks_and_notes", processed)

    category_codes = {
        name: "DEMO_CAT_%02d" % index
        for index, name in enumerate(CATEGORIES, 1)
    }
    category_count = count(CATEGORY_TYPE)
    if CREATE_CATEGORIES and category_count == 0:
        records(CATEGORY_TYPE, [
            fields(category_columns, category_codes[name], name,
                   "Synthetic asset category for interface demonstrations")
            for name in CATEGORIES
        ])
        return report("categories_created", len(category_codes))
    if CREATE_CATEGORIES and category_count != len(category_codes):
        raise RuntimeError("Expected %d categories, found %d" % (len(category_codes), category_count))

    if CREATE_ASSETS and category_count != len(category_codes):
        raise RuntimeError("Create the demo asset categories before assets")
    if CREATE_ASSETS and asset_count > ASSETS:
        raise RuntimeError("Asset count exceeds the demo target")
    asset_link_count = count(episode_asset["instance_type"]) if LINK_EPISODE_ASSETS else 0
    if LINK_EPISODE_ASSETS and asset_link_count > asset_count:
        raise RuntimeError("Episode-Asset link count exceeds asset count")
    linked = 0
    while LINK_EPISODE_ASSETS and asset_link_count < asset_count:
        end = min(asset_link_count + 100, asset_count)
        for index in range(asset_link_count + 1, end + 1):
            episode = sobject(EPISODE_TYPE, "DEMO_EP%03d" % ((index - 1) % EPISODES + 1))
            asset = sobject(ASSET_TYPE, "DEMO_AST%04d" % index)
            link(episode_asset, EPISODE_TYPE, episode, asset)
        linked += end - asset_link_count
        asset_link_count = end
        if time.time() - started >= MAX_SECONDS_PER_RUN:
            return report("episode_asset_links", linked)
    created = 0
    while CREATE_ASSETS and asset_count < ASSETS:
        end = min(asset_count + 100, ASSETS)
        asset_rows = []
        category_names = tuple(CATEGORIES)
        for index in range(asset_count + 1, end + 1):
            category = category_names[(index - 1) % len(category_names)]
            label = CATEGORIES[category][(index - 1) // len(category_names) % len(CATEGORIES[category])]
            variant = random.Random(SEED + 100000 + index).choice(ASSET_VARIANTS)
            name = "%s — %s %s %04d" % (category, variant, label, index)
            asset_rows.append(fields(
                asset_columns, "DEMO_AST%04d" % index, name,
                "Synthetic %s asset for interface demonstrations" % category,
                **{category_column: category_codes[category]},
            ))
        records(ASSET_TYPE, asset_rows)
        if LINK_EPISODE_ASSETS:
            for index in range(asset_count + 1, end + 1):
                episode = sobject(EPISODE_TYPE, "DEMO_EP%03d" % ((index - 1) % EPISODES + 1))
                asset = sobject(ASSET_TYPE, "DEMO_AST%04d" % index)
                link(episode_asset, EPISODE_TYPE, episode, asset)
            linked += end - asset_count
        created += end - asset_count
        asset_count = end
        if time.time() - started >= MAX_SECONDS_PER_RUN:
            return report("assets_created", created)

    if CREATE_TEXTURES and texture_count > TEXTURES:
        raise RuntimeError("Texture count exceeds the demo target")
    texture_link_count = count(asset_texture["instance_type"]) if LINK_ASSET_TEXTURES else 0
    if LINK_ASSET_TEXTURES and texture_link_count > texture_count:
        raise RuntimeError("Asset-Texture link count exceeds texture count")
    linked = 0
    while LINK_ASSET_TEXTURES and texture_link_count < texture_count:
        end = min(texture_link_count + 100, texture_count)
        for index in range(texture_link_count + 1, end + 1):
            asset = sobject(ASSET_TYPE, "DEMO_AST%04d" % ((index - 1) % ASSETS + 1))
            texture = sobject(TEXTURE_TYPE, "DEMO_TEX%04d" % index)
            link(asset_texture, ASSET_TYPE, asset, texture)
        linked += end - texture_link_count
        texture_link_count = end
        if time.time() - started >= MAX_SECONDS_PER_RUN:
            return report("asset_texture_links", linked)
    created = 0
    while CREATE_TEXTURES and texture_count < TEXTURES:
        end = min(texture_count + 100, TEXTURES)
        texture_rows = []
        for index in range(texture_count + 1, end + 1):
            asset = sobject(ASSET_TYPE, "DEMO_AST%04d" % ((index - 1) % ASSETS + 1))
            kind = random.Random(SEED + 200000 + index).choice(TEXTURE_KINDS)
            texture_rows.append(fields(
                texture_columns, "DEMO_TEX%04d" % index,
                "%s — %s" % (asset.get_value("name"), kind),
                "Synthetic %s texture" % kind,
            ))
        records(TEXTURE_TYPE, texture_rows)
        if LINK_ASSET_TEXTURES:
            for index in range(texture_count + 1, end + 1):
                asset = sobject(ASSET_TYPE, "DEMO_AST%04d" % ((index - 1) % ASSETS + 1))
                texture = sobject(TEXTURE_TYPE, "DEMO_TEX%04d" % index)
                link(asset_texture, ASSET_TYPE, asset, texture)
            linked += end - texture_count
        created += end - texture_count
        texture_count = end
        if time.time() - started >= MAX_SECONDS_PER_RUN:
            return report("textures_created", created)

    for search_type, prefix, total, tag_pool, salt in (
            (EPISODE_TYPE, "DEMO_EP", EPISODES, EPISODE_TAGS, 300000),
            (ASSET_TYPE, "DEMO_AST", ASSETS, ASSET_TAGS, 400000)):
        if search_type == EPISODE_TYPE and not TAG_EPISODES:
            continue
        if search_type == ASSET_TYPE and not TAG_ASSETS:
            continue
        columns = episode_columns if search_type == EPISODE_TYPE else asset_columns
        column = next((name for name in ("keywords", "tags", "tag") if name in columns), None)
        if not column:
            raise RuntimeError("Add a keywords/tags/tag column to %s before enrichment" % search_type)
        search = Search(search_type)
        search.add_filter("code", prefix + "%", op="like")
        processed = 0
        for item in sorted(search.get_sobjects(), key=lambda row: row.get_value("code")):
            code = str(item.get_value("code"))
            suffix = code[len(prefix):]
            if not suffix.isdigit() or not 1 <= int(suffix) <= total:
                continue
            index = int(suffix)
            rng = random.Random(SEED + salt + index)
            tags = rng.sample(tag_pool, rng.randint(2, 5))
            if search_type == ASSET_TYPE:
                category = tuple(CATEGORIES)[(index - 1) % len(CATEGORIES)]
                tags.insert(0, category.lower().replace(" ", "-"))
            if add_tags(item, column, tags):
                processed += 1
                if time.time() - started >= MAX_SECONDS_PER_RUN:
                    break
        if processed:
            return report("episode_tags" if search_type == EPISODE_TYPE else "asset_tags", processed)

    if CREATE_EPISODE_NOTES:
        episode_search = Search(EPISODE_TYPE)
        episode_search.add_filter("code", "DEMO_EP%", op="like")
        episodes = sorted(episode_search.get_sobjects(), key=lambda row: row.get_value("code"))
        done_search = Search("sthpw/note")
        done_search.add_filter("project_code", PROJECT_CODE)
        done_search.add_filter("search_type", EPISODE_TYPE + "%", op="like")
        done_search.add_filter("note", EPISODE_DISCUSSION_DONE)
        episode_done = {note.get_value("search_id") for note in done_search.get_sobjects()}
        logins = sorted(name for name in login_objects if name != "guest")
        if episodes and len(logins) < 2:
            raise RuntimeError("At least two TACTIC users are needed for demo notes")
        processed = 0
        for episode in episodes:
            if episode.get_id() in episode_done:
                continue
            code = str(episode.get_value("code"))
            suffix = code[len("DEMO_EP"):]
            if not suffix.isdigit() or not 1 <= int(suffix) <= EPISODES:
                continue
            task_search = Search("sthpw/task")
            task_search.add_filter("project_code", PROJECT_CODE)
            task_search.add_filter("search_type", EPISODE_TYPE + "%", op="like")
            task_search.add_filter("search_id", episode.get_id())
            processes = list(dict.fromkeys(
                task.get_value("process") for task in task_search.get_sobjects()
                if task.get_value("process")
            ))
            if not processes:
                raise RuntimeError("Episode %s has no tasks to discuss" % code)
            rng = random.Random(SEED + 600000 + int(suffix))
            episode_key = key(EPISODE_TYPE, code)
            note_search = Search("sthpw/note")
            note_search.add_filter("project_code", PROJECT_CODE)
            note_search.add_filter("search_type", EPISODE_TYPE + "%", op="like")
            note_search.add_filter("search_id", episode.get_id())
            existing_notes = {
                (note.get_value("process"), note.get_value("note"))
                for note in note_search.get_sobjects()
            }
            note_rows = []
            for process in processes[:2]:
                participants = rng.sample(logins, 2)
                for position in range(rng.randint(3, 5)):
                    text = "[DEMO] Episode review: " + rng.choice(NOTE_VARIANTS[position])
                    if (process, text) not in existing_notes:
                        note_rows.append({
                            "process": process, "context": process,
                            "login": participants[position % 2], "note": text,
                        })
            if note_rows:
                records("sthpw/note", note_rows, parent_key=episode_key)
            records("sthpw/note", [{
                "process": processes[0], "context": processes[0],
                "login": logins[0], "note": EPISODE_DISCUSSION_DONE,
            }], parent_key=episode_key)
            processed += 1
            if time.time() - started >= MAX_SECONDS_PER_RUN:
                break
        if processed:
            return report("episode_discussions", processed)

    if CREATE_ASSET_TASKS or CREATE_ASSET_NOTES:
        asset_search = Search(ASSET_TYPE)
        asset_search.add_filter("code", "DEMO_AST%", op="like")
        assets = sorted(asset_search.get_sobjects(), key=lambda row: row.get_value("code"))
        if assets:
            logins = sorted(name for name in login_objects if name != "guest")
            if len(logins) < 2:
                raise RuntimeError("At least two TACTIC users are needed for demo tasks and notes")
            pipeline_search = Search("sthpw/pipeline")
            pipeline_search.add_filter("search_type", ASSET_TYPE)
            pipeline_search.add_filter("project_code", PROJECT_CODE)
            pipelines = pipeline_search.get_sobjects()
            processes = list(dict.fromkeys(pipelines[0].get_process_names())) if pipelines else []
            if not processes:
                raise RuntimeError("Configure an Asset pipeline with processes before seeding tasks")
            task_search = Search("sthpw/task")
            task_search.add_filter("project_code", PROJECT_CODE)
            task_search.add_filter("search_type", ASSET_TYPE + "%", op="like")
            existing_tasks = {
                (item.get_value("search_id"), item.get_value("process"), item.get_value("description"))
                for item in task_search.get_sobjects()
            }
            completed = set()
            if CREATE_ASSET_NOTES:
                completed_search = Search("sthpw/note")
                completed_search.add_filter("project_code", PROJECT_CODE)
                completed_search.add_filter("search_type", ASSET_TYPE + "%", op="like")
                completed_search.add_filter("note", ASSET_DISCUSSION_DONE)
                completed = {item.get_value("search_id") for item in completed_search.get_sobjects()}
            processed = 0
            for asset in assets:
                code = str(asset.get_value("code"))
                suffix = code[len("DEMO_AST"):]
                if not suffix.isdigit() or not 1 <= int(suffix) <= ASSETS:
                    continue
                index = int(suffix)
                rng = random.Random(SEED + 500000 + index)
                selected = rng.sample(processes, rng.randint(1, min(3, len(processes))))
                descriptions = rng.sample(TASK_TEXTS, len(selected))
                asset_key = key(ASSET_TYPE, code)
                desired_tasks = [
                    {"process": process, "assigned": rng.choice(logins),
                     "description": "[DEMO] " + description}
                    for process, description in zip(selected, descriptions)
                ]
                changed = False
                if CREATE_ASSET_TASKS:
                    missing = [row for row in desired_tasks
                               if (asset.get_id(), row["process"], row["description"])
                               not in existing_tasks]
                    if missing:
                        records("sthpw/task", missing, parent_key=asset_key)
                        existing_tasks.update(
                            (asset.get_id(), row["process"], row["description"])
                            for row in missing
                        )
                        changed = True
                if CREATE_ASSET_NOTES and asset.get_id() not in completed:
                    if not any(identity[0] == asset.get_id() for identity in existing_tasks):
                        raise RuntimeError("Asset %s needs tasks before notes" % code)
                    note_search = Search("sthpw/note")
                    note_search.add_filter("project_code", PROJECT_CODE)
                    note_search.add_filter("search_type", ASSET_TYPE + "%", op="like")
                    note_search.add_filter("search_id", asset.get_id())
                    existing_notes = {
                        (item.get_value("process"), item.get_value("note"))
                        for item in note_search.get_sobjects()
                    }
                    note_rows = []
                    for process in selected:
                        participants = rng.sample(logins, 2)
                        for position in range(rng.randint(3, 6)):
                            text = "[DEMO] " + rng.choice(NOTE_VARIANTS[position])
                            if (process, text) not in existing_notes:
                                note_rows.append({
                                    "process": process, "context": process,
                                    "login": participants[position % 2], "note": text,
                                })
                                existing_notes.add((process, text))
                    if note_rows:
                        records("sthpw/note", note_rows, parent_key=asset_key)
                    records("sthpw/note", [{
                        "process": selected[-1], "context": selected[-1],
                        "login": logins[0], "note": ASSET_DISCUSSION_DONE,
                    }], parent_key=asset_key)
                    changed = True
                if changed:
                    processed += 1
                if processed and time.time() - started >= MAX_SECONDS_PER_RUN:
                    break
            if processed:
                return report("asset_tasks_and_notes", processed)
    return report("complete")


# TACTIC wraps Server Python source in a function; its result appears in the editor.
return seed_project()
