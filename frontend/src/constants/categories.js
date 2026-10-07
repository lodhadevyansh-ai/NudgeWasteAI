export const STATUTORY_CATEGORIES = {
  WET: 'Wet',
  DRY: 'Dry',
  SANITARY: 'Sanitary',
  SPECIAL_CARE: 'Special Care',
};

export const CATEGORY_DETAILS = {
  [STATUTORY_CATEGORIES.WET]: {
    name: 'Wet Waste',
    binName: 'Green Bin',
    binColor: '#10B981', // Emerald / Green
    bgColor: '#ECFDF5',
    borderColor: '#A7F3D0',
    textColor: '#065F46',
    description: 'Organic, biodegradable, and kitchen food waste.',
    examples: ['Fruit & vegetable peels', 'Food leftovers', 'Tea leaves & coffee grounds', 'Garden leaves & flowers'],
    disposalGuide: 'Place in Green Bin for municipal composting and bio-gas generation.',
  },
  [STATUTORY_CATEGORIES.DRY]: {
    name: 'Dry Waste',
    binName: 'Blue Bin',
    binColor: '#3B82F6', // Blue
    bgColor: '#EFF6FF',
    borderColor: '#BFDBFE',
    textColor: '#1E40AF',
    description: 'Clean, recyclable non-biodegradable packaging & materials.',
    examples: ['Plastic bottles & containers', 'Paper & cardboard', 'Glass bottles', 'Clean metal cans'],
    disposalGuide: 'Rinse and dry items before placing in Blue Bin for material recycling.',
  },
  [STATUTORY_CATEGORIES.SANITARY]: {
    name: 'Sanitary Waste',
    binName: 'Red / Marked Bin',
    binColor: '#EF4444', // Red
    bgColor: '#FEF2F2',
    borderColor: '#FECACA',
    textColor: '#991B1B',
    description: 'Personal hygiene and biomedical waste items.',
    examples: ['Diapers & sanitary pads', 'Used tissues & cotton swabs', 'Bandages & medical dressings'],
    disposalGuide: 'Wrap securely in newspaper marked with a red cross and hand over separately.',
  },
  [STATUTORY_CATEGORIES.SPECIAL_CARE]: {
    name: 'Special Care / E-Waste',
    binName: 'Black Bin',
    binColor: '#1E293B', // Dark Slate
    bgColor: '#F1F5F9',
    borderColor: '#CBD5E1',
    textColor: '#0F172A',
    description: 'Hazardous, electronic, or toxic municipal waste items.',
    examples: ['Batteries & electronic gadgets', 'Fluorescent bulbs & tubes', 'Paint cans & chemicals', 'Expired medicines'],
    disposalGuide: 'Store safely and hand over to designated E-Waste & hazardous waste collectors.',
  },
};
