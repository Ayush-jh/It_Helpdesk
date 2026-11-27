
db = db.getSiblingDB("smart_office");

db.resource_configs.drop();

const configs = [
  {
    resource_id: 1,                 
    type: "desk",
    desk_code: "D-101",
    zone: "Open Hot Desks",
    floor: 1,
    amenities: [
      { name: "Standard Monitor", count: 1 },
      { name: "Ergonomic Chair", count: 1 }
    ],
    metadata: { near_window: false, quiet: false, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 2,
    type: "desk",
    desk_code: "D-102",
    zone: "Open Hot Desks",
    floor: 1,
    amenities: [
      { name: "Dual Monitor", count: 2 },
      { name: "Ergonomic Chair", count: 1 },
      { name: "USB-C Dock", count: 1 },
      { name: "Wireless Charger", count: 1 }
    ],
    metadata: { near_window: true, quiet: false, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 3,
    type: "desk",
    desk_code: "D-103",
    zone: "Open Hot Desks",
    floor: 1,
    amenities: [
      { name: "Standard Monitor", count: 1 },
      { name: "Ergonomic Chair", count: 1 }
    ],
    metadata: { near_window: false, quiet: false, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 4,
    type: "desk",
    desk_code: "D-201",
    zone: "Quiet Zone",
    floor: 1,
    amenities: [
      { name: "Dual Monitor", count: 2 },
      { name: "Noise-Cancelling Headset", count: 1 },
      { name: "Ergonomic Chair", count: 1 }
    ],
    metadata: { near_window: true, quiet: true, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 5,
    type: "desk",
    desk_code: "D-202",
    zone: "Quiet Zone",
    floor: 1,
    amenities: [
      { name: "Standard Monitor", count: 1 },
      { name: "Ergonomic Chair", count: 1 }
    ],
    metadata: { near_window: false, quiet: true, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 6,
    type: "meeting_room",
    desk_code: "MR-301",
    zone: "Meeting Wing",
    floor: 2,
    amenities: [
      { name: "Projector", count: 1 },
      { name: "Whiteboard", count: 2 },
      { name: "Video Conference", count: 1 },
      { name: "Speakerphone", count: 1 },
      { name: "HDMI Cable", count: 2 }
    ],
    metadata: { seats: 20, bookable_hours: "08:00-20:00", requires_approval: false },
    updated_at: new Date()
  },
  {
    resource_id: 7,
    type: "meeting_room",
    desk_code: "MR-302",
    zone: "Meeting Wing",
    floor: 2,
    amenities: [
      { name: "TV Screen", count: 1 },
      { name: "Whiteboard", count: 1 },
      { name: "Speakerphone", count: 1 }
    ],
    metadata: { seats: 12, bookable_hours: "08:00-20:00", requires_approval: false },
    updated_at: new Date()
  },
  {
    resource_id: 8,
    type: "cabin",
    desk_code: "C-401",
    zone: "Cabins",
    floor: 2,
    amenities: [
      { name: "Private Door", count: 1 },
      { name: "Dual Monitor", count: 2 },
      { name: "Ergonomic Chair", count: 1 }
    ],
    metadata: { seats: 4, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 9,
    type: "cabin",
    desk_code: "C-402",
    zone: "Cabins",
    floor: 2,
    amenities: [
      { name: "Private Door", count: 1 },
      { name: "Dual Monitor", count: 2 },
      { name: "Ergonomic Chair", count: 2 }
    ],
    metadata: { seats: 6, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 10,
    type: "desk",
    desk_code: "D-501",
    zone: "Collab",
    floor: 3,
    amenities: [
      { name: "Dual Monitor", count: 2 },
      { name: "USB-C Dock", count: 1 }
    ],
    metadata: { near_window: true, quiet: false, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 11,
    type: "desk",
    desk_code: "D-502",
    zone: "Collab",
    floor: 3,
    amenities: [
      { name: "Standard Monitor", count: 1 },
      { name: "Ergonomic Chair", count: 1 }
    ],
    metadata: { near_window: false, quiet: false, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 12,
    type: "desk",
    desk_code: "D-601",
    zone: "Focus",
    floor: 3,
    amenities: [
      { name: "Dual Monitor", count: 2 },
      { name: "Noise-Cancelling Headset", count: 1 }
    ],
    metadata: { near_window: false, quiet: true, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  },
  {
    resource_id: 13,
    type: "desk",
    desk_code: "D-602",
    zone: "Focus",
    floor: 3,
    amenities: [
      { name: "Standard Monitor", count: 1 },
      { name: "Ergonomic Chair", count: 1 }
    ],
    metadata: { near_window: false, quiet: true, bookable_hours: "07:00-22:00" },
    updated_at: new Date()
  }
];

db.resource_configs.insertMany(configs);


db.resource_configs.createIndex({ "amenities.name": 1 });
db.resource_configs.createIndex({ resource_id: 1 }, { unique: true });
db.resource_configs.createIndex({ zone: 1, type: 1 });

print("✓ Inserted " + db.resource_configs.countDocuments() + " resource documents.");