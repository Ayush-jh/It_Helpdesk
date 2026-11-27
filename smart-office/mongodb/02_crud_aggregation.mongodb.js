// ============================================================
// 02_crud_aggregation.js — CRUD + Aggregation demo
// ============================================================

db = db.getSiblingDB("smart_office");

print("\n========== CRUD DEMO ==========\n");

// ---------- CREATE ----------
print("→ CREATE: Add a new desk with standing desk + dual monitor");
db.resource_configs.insertOne({
  resource_id: 14,
  type: "desk",
  desk_code: "D-104",
  zone: "Open Hot Desks",
  floor: 1,
  amenities: [
    { name: "Standing Desk", count: 1 },
    { name: "Dual Monitor", count: 2 },
    { name: "Ergonomic Chair", count: 1 }
  ],
  metadata: { near_window: true, quiet: false, bookable_hours: "07:00-22:00" },
  updated_at: new Date()
});

// ---------- READ ----------
print("\n→ READ: All resources with a Projector");
db.resource_configs
  .find({ "amenities.name": "Projector" }, { _id: 0, resource_id: 1, desk_code: 1, zone: 1 })
  .forEach(printjson);

// ---------- UPDATE ----------
print("\n→ UPDATE: Add 'Wireless Charger' to D-102 (resource_id 2)");
db.resource_configs.updateOne(
  { resource_id: 2 },
  {
    $push: { amenities: { name: "Wireless Charger", count: 1 } },
    $set:  { updated_at: new Date() }
  }
);

print("\n→ UPDATE result (D-102 amenities):");
db.resource_configs
  .findOne({ resource_id: 2 }, { _id: 0, desk_code: 1, amenities: 1 })
  .amenities.forEach(a => print("   - " + a.name + " x" + a.count));

// ---------- UPDATE (decrement/remove) ----------
print("\n→ UPDATE: Remove 'HDMI Cable' from MR-301 (resource_id 6)");
db.resource_configs.updateOne(
  { resource_id: 6 },
  { $pull: { amenities: { name: "HDMI Cable" } }, $set: { updated_at: new Date() } }
);

// ---------- DELETE ----------
print("\n→ DELETE: Remove the test desk D-104 (resource_id 14)");
const del = db.resource_configs.deleteOne({ resource_id: 14 });
print("   deletedCount = " + del.deletedCount);

print("\n========== AGGREGATION DEMO ==========\n");

// ---------- AGG 1: Count resources per zone that offer Dual Monitor ----------
print("→ AGG 1: Desks per zone offering 'Dual Monitor'");
db.resource_configs.aggregate([
  { $match: { "amenities.name": "Dual Monitor" } },
  { $group: { _id: "$zone", resource_count: { $sum: 1 } } },
  { $sort: { resource_count: -1 } }
]).forEach(printjson);

// ---------- AGG 2: Total amenity inventory per zone ----------
print("\n→ AGG 2: Total amenity units (across all resources) per zone");
db.resource_configs.aggregate([
  { $unwind: "$amenities" },
  { $group: {
      _id: "$zone",
      total_units: { $sum: "$amenities.count" },
      distinct_amenities: { $addToSet: "$amenities.name" }
  }},
  { $project: {
      zone: "$_id",
      _id: 0,
      total_units: 1,
      distinct_count: { $size: "$distinct_amenities" }
  }},
  { $sort: { total_units: -1 } }
]).forEach(printjson);

// ---------- AGG 3: Top-3 most common amenities across all resources ----------
print("\n→ AGG 3: Top-3 most common amenities");
db.resource_configs.aggregate([
  { $unwind: "$amenities" },
  { $group: { _id: "$amenities.name", occurrences: { $sum: 1 } } },
  { $sort: { occurrences: -1 } },
  { $limit: 3 }
]).forEach(printjson);

// ---------- AGG 4: Resources that have BOTH Projector AND Video Conference ----------
print("\n→ AGG 4: Meeting rooms with Projector AND Video Conference");
db.resource_configs.aggregate([
  { $match: {
      type: "meeting_room",
      amenities: { $all: [
        { $elemMatch: { name: "Projector" } },
        { $elemMatch: { name: "Video Conference" } }
      ]}
  }},
  { $project: { _id: 0, desk_code: 1, zone: 1, seats: "$metadata.seats" } }
]).forEach(printjson);

// ---------- AGG 5: Amenity audit — which resources have ≥ 3 amenities ----------
print("\n→ AGG 5: Resources with 3+ amenities");
db.resource_configs.aggregate([
  { $project: {
      _id: 0,
      desk_code: 1,
      zone: 1,
      amenity_count: { $size: "$amenities" }
  }},
  { $match: { amenity_count: { $gte: 3 } } },
  { $sort: { amenity_count: -1 } }
]).forEach(printjson);

print("\n✓ CRUD + aggregation demo completed.");