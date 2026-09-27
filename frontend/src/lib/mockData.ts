export interface InventoryItem {
  id: string;
  name: string;
  category: 'Produce' | 'Dairy & Eggs' | 'Meat & Poultry' | 'Dry Goods & Grains' | 'Bakery' | 'Prepared Bases';
  currentStock: number;
  unit: 'kg' | 'liters' | 'units' | 'boxes';
  reorderLevel: number;
  lotNumber: string;
  expiryDate: string;
  daysRemaining: number;
  storageTemp: 'Chilled (0-4°C)' | 'Frozen (-18°C)' | 'Dry Ambient (15-22°C)';
  supplier: string;
  status: 'optimal' | 'expiring_soon' | 'critical' | 'depleted';
  unitCostUSD: number;
}

export interface MenuItem {
  id: string;
  day: 'Monday' | 'Tuesday' | 'Wednesday' | 'Thursday' | 'Friday' | 'Saturday' | 'Sunday';
  mealService: 'Breakfast' | 'Lunch' | 'Dinner' | 'Late Night Service';
  dishName: string;
  plannedPortions: number;
  dietaryCategory: 'Standard' | 'Vegetarian' | 'Vegan' | 'Gluten-Free' | 'Halal';
  allergens: string[];
  prepLeadTimeMins: number;
  estimatedCostPerPortion: number;
  status: 'Draft' | 'Approved' | 'In Production' | 'Archived';
}

export interface ProductionBatch {
  id: string;
  batchNumber: string;
  recipeName: string;
  station: 'Cold Prep Line 1' | 'Hot Kitchen Range A' | 'Bakery Ovens' | 'Assembly Bay 2';
  plannedQty: number;
  unit: string;
  status: 'Scheduled' | 'Prepping' | 'Cooking' | 'Holding' | 'Completed';
  targetTempC: number;
  currentTempC: number;
  headChef: string;
  startTime: string;
  estEndTime: string;
  haccpCompliant: boolean;
}

export interface ConsumptionLog {
  id: string;
  date: string;
  mealService: string;
  plannedHeadcount: number;
  actualHeadcount: number;
  variancePercentage: number;
  totalFoodPreparedKg: number;
  totalConsumedKg: number;
  unconsumedKg: number;
  residualSurplusDivertedKg: number;
  notes: string;
}

export interface WasteRecord {
  id: string;
  timestamp: string;
  category: 'Preparation Trimmings' | 'Plate Scraps' | 'Spoilage & Expiry' | 'Overproduction Surplus' | 'Equipment Failure';
  weightKg: number;
  costUSD: number;
  ghgKgCO2e: number;
  department: string;
  rootCause: string;
  loggedBy: string;
  epaHierarchyTier: 'Prevention' | 'Feed Hungry People' | 'Industrial Valorization' | 'Compost' | 'Landfill';
}

export interface ForecastPoint {
  date: string;
  dayName: string;
  historicalDemand: number;
  predictedDemand: number;
  lowerBound: number;
  upperBound: number;
  weather: 'Sunny 24°C' | 'Rainy 18°C' | 'Clear 22°C' | 'Stormy 16°C';
  isHolidayOrEvent: boolean;
  eventDescription?: string;
  confidenceScore: number;
}

export interface OptimizerRecommendation {
  id: string;
  menuDish: string;
  baselineDemandPortions: number;
  recommendedBatchPortions: number;
  variancePct: number;
  safetyBufferPct: number;
  expectedWasteReductionKg: number;
  estimatedCostSavingsUSD: number;
  confidenceScore: number;
  rationale: string;
  applied: boolean;
}

export interface RecipientMatch {
  id: string;
  recipientOrg: string;
  facilityType: 'Soup Kitchen' | 'Homeless Shelter' | 'Youth Refuge' | 'Community Pantry' | 'Disaster Relief Base' | 'Food Bank';
  distanceKm: number;
  transitTimeMins: number;
  demandCapacityKg: number;
  affinityScorePct: number;
  coldStorageAvailable: boolean;
  dietaryMatch: boolean;
  contactPerson: string;
  contactPhone: string;
  status: 'Pending Match' | 'Assigned' | 'Dispatched' | 'Completed';
}

export interface DonationManifest {
  manifestId: string;
  trackingNumber: string;
  donorOrg: string;
  recipientOrg: string;
  totalWeightKg: number;
  mealPortions: number;
  category: string;
  storageTemp: string;
  transitTemperatureC: number;
  departureTime: string;
  estimatedArrival: string;
  courierDriver: string;
  vehiclePlate: string;
  status: 'Manifest Created' | 'Loading' | 'In Transit' | 'Delivered' | 'Verified';
  haccpCheckPassed: boolean;
  digitalSignatures: {
    donorSigned: boolean;
    courierSigned: boolean;
    recipientSigned: boolean;
  };
}

export interface DriverWaypoint {
  id: string;
  type: 'Pickup' | 'Dropoff' | 'Depot';
  name: string;
  address: string;
  timeWindow: string;
  cargoWeightKg: number;
  completed: boolean;
  temperatureTargetC: string;
  notes: string;
}

export interface KnowledgeArticle {
  id: string;
  title: string;
  source: 'FDA Food Code 2022' | 'Bill Emerson Good Samaritan Act' | 'HACCP Standard' | 'Cold Chain SOP';
  category: 'Food Safety' | 'Legal & Liability' | 'Logistics' | 'Sanitation';
  excerpt: string;
  fullContent: string;
  keyRule: string;
  lastUpdated: string;
}

export interface AuditLogEntry {
  id: string;
  timestamp: string;
  actor: string;
  role: string;
  action: string;
  entity: string;
  ipAddress: string;
  sha256Hash: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  timestamp: string;
  category: 'urgent' | 'logistics' | 'production' | 'audit' | 'system';
  read: boolean;
  actionTarget?: string;
}

// -------------------------------------------------------------
// CORE MOCK DATASETS
// -------------------------------------------------------------

export const KPI_METRICS_DATA = {
  foodSaved: { value: '48,250', unit: 'kg', trend: { percentage: 14.8, isPositive: true, periodText: 'vs last month' } },
  wasteReduced: { value: '38.4', unit: '%', trend: { percentage: 6.2, isPositive: true, periodText: 'from baseline' } },
  mealsRedistributed: { value: '102,680', unit: 'meals', trend: { percentage: 18.5, isPositive: true, periodText: 'total rescued' } },
  peopleServed: { value: '29,400', unit: 'beneficiaries', trend: { percentage: 12.1, isPositive: true, periodText: 'active reach' } },
  estimatedValuePreserved: { value: '$142,850', unit: 'USD', trend: { percentage: 16.4, isPositive: true, periodText: 'recovered value' } },
  environmentalImpact: { value: '120.6', unit: 't CO₂e avoided', trend: { percentage: 21.0, isPositive: true, periodText: 'GHG reduction' } },
};

export const MOCK_INVENTORY: InventoryItem[] = [
  {
    id: 'inv-101',
    name: 'Fresh Atlantic Salmon Fillets',
    category: 'Meat & Poultry',
    currentStock: 18.5,
    unit: 'kg',
    reorderLevel: 25.0,
    lotNumber: 'LOT-2026-SLM-09',
    expiryDate: '2026-09-28',
    daysRemaining: 1,
    storageTemp: 'Chilled (0-4°C)',
    supplier: 'Pacific Coast Seafoods',
    status: 'critical',
    unitCostUSD: 19.5,
  },
  {
    id: 'inv-102',
    name: 'Organic Whole Milk (3.5%)',
    category: 'Dairy & Eggs',
    currentStock: 64.0,
    unit: 'liters',
    reorderLevel: 40.0,
    lotNumber: 'LOT-2026-MLK-88',
    expiryDate: '2026-09-29',
    daysRemaining: 2,
    storageTemp: 'Chilled (0-4°C)',
    supplier: 'Meadow Gold Dairy',
    status: 'expiring_soon',
    unitCostUSD: 1.85,
  },
  {
    id: 'inv-103',
    name: 'Roma Cooking Tomatoes',
    category: 'Produce',
    currentStock: 145.0,
    unit: 'kg',
    reorderLevel: 60.0,
    lotNumber: 'LOT-2026-TOM-44',
    expiryDate: '2026-09-30',
    daysRemaining: 3,
    storageTemp: 'Dry Ambient (15-22°C)',
    supplier: 'Valley Fresh Agri',
    status: 'optimal',
    unitCostUSD: 2.1,
  },
  {
    id: 'inv-104',
    name: 'Artisan Brioche Burger Buns',
    category: 'Bakery',
    currentStock: 280,
    unit: 'units',
    reorderLevel: 100,
    lotNumber: 'LOT-2026-BUN-12',
    expiryDate: '2026-09-28',
    daysRemaining: 1,
    storageTemp: 'Dry Ambient (15-22°C)',
    supplier: 'Golden Crust Boulangerie',
    status: 'critical',
    unitCostUSD: 0.65,
  },
  {
    id: 'inv-105',
    name: 'Grade-A Boneless Chicken Thighs',
    category: 'Meat & Poultry',
    currentStock: 82.0,
    unit: 'kg',
    reorderLevel: 50.0,
    lotNumber: 'LOT-2026-CHK-71',
    expiryDate: '2026-10-02',
    daysRemaining: 5,
    storageTemp: 'Frozen (-18°C)',
    supplier: 'Midwest Poultry Supply',
    status: 'optimal',
    unitCostUSD: 6.8,
  },
  {
    id: 'inv-106',
    name: 'Jasmine Fragrant Rice (Bulk Sack)',
    category: 'Dry Goods & Grains',
    currentStock: 350.0,
    unit: 'kg',
    reorderLevel: 150.0,
    lotNumber: 'LOT-2026-RIC-02',
    expiryDate: '2027-04-15',
    daysRemaining: 200,
    storageTemp: 'Dry Ambient (15-22°C)',
    supplier: 'Global Grains Alliance',
    status: 'optimal',
    unitCostUSD: 1.45,
  },
  {
    id: 'inv-107',
    name: 'Heavy Whipping Cream 36%',
    category: 'Dairy & Eggs',
    currentStock: 8.0,
    unit: 'liters',
    reorderLevel: 20.0,
    lotNumber: 'LOT-2026-CRM-31',
    expiryDate: '2026-09-28',
    daysRemaining: 1,
    storageTemp: 'Chilled (0-4°C)',
    supplier: 'Meadow Gold Dairy',
    status: 'critical',
    unitCostUSD: 4.2,
  },
];

export const MOCK_MENU: MenuItem[] = [
  {
    id: 'menu-1',
    day: 'Monday',
    mealService: 'Lunch',
    dishName: 'Mediterranean Lemon Herb Grilled Chicken',
    plannedPortions: 450,
    dietaryCategory: 'Standard',
    allergens: ['Dairy (Marinade)'],
    prepLeadTimeMins: 90,
    estimatedCostPerPortion: 4.15,
    status: 'Approved',
  },
  {
    id: 'menu-2',
    day: 'Monday',
    mealService: 'Lunch',
    dishName: 'Quinoa & Roasted Veggie Mezze Bowl',
    plannedPortions: 160,
    dietaryCategory: 'Vegan',
    allergens: ['Sesame (Tahini)'],
    prepLeadTimeMins: 45,
    estimatedCostPerPortion: 2.85,
    status: 'Approved',
  },
  {
    id: 'menu-3',
    day: 'Monday',
    mealService: 'Dinner',
    dishName: 'Pan-Seared Salmon with Dill Cream & Wild Rice',
    plannedPortions: 380,
    dietaryCategory: 'Gluten-Free',
    allergens: ['Fish', 'Dairy'],
    prepLeadTimeMins: 110,
    estimatedCostPerPortion: 6.9,
    status: 'In Production',
  },
  {
    id: 'menu-4',
    day: 'Tuesday',
    mealService: 'Lunch',
    dishName: 'Homestyle Beef Lasagna al Forno',
    plannedPortions: 520,
    dietaryCategory: 'Standard',
    allergens: ['Gluten', 'Dairy', 'Eggs'],
    prepLeadTimeMins: 150,
    estimatedCostPerPortion: 3.8,
    status: 'Approved',
  },
  {
    id: 'menu-5',
    day: 'Wednesday',
    mealService: 'Dinner',
    dishName: 'Chickpea & Coconut Milk Curry with Basmati',
    plannedPortions: 340,
    dietaryCategory: 'Vegan',
    allergens: [],
    prepLeadTimeMins: 60,
    estimatedCostPerPortion: 2.2,
    status: 'Draft',
  },
];

export const MOCK_PRODUCTION_BATCHES: ProductionBatch[] = [
  {
    id: 'pb-01',
    batchNumber: 'BATCH-2026-0927-A',
    recipeName: 'Mediterranean Lemon Herb Chicken',
    station: 'Hot Kitchen Range A',
    plannedQty: 450,
    unit: 'portions',
    status: 'Holding',
    targetTempC: 74,
    currentTempC: 76.5,
    headChef: 'Chef Marcus Vance',
    startTime: '10:15 AM',
    estEndTime: '12:00 PM',
    haccpCompliant: true,
  },
  {
    id: 'pb-02',
    batchNumber: 'BATCH-2026-0927-B',
    recipeName: 'Steamed Jasmine Rice with Coriander',
    station: 'Hot Kitchen Range A',
    plannedQty: 75,
    unit: 'kg',
    status: 'Completed',
    targetTempC: 65,
    currentTempC: 68.0,
    headChef: 'Sous Chef Sarah Chen',
    startTime: '10:45 AM',
    estEndTime: '11:45 AM',
    haccpCompliant: true,
  },
  {
    id: 'pb-03',
    batchNumber: 'BATCH-2026-0927-C',
    recipeName: 'Garden Fresh Mezze Salad Mix',
    station: 'Cold Prep Line 1',
    plannedQty: 180,
    unit: 'portions',
    status: 'Holding',
    targetTempC: 4,
    currentTempC: 3.2,
    headChef: 'Chef Elena Rostova',
    startTime: '11:00 AM',
    estEndTime: '11:50 AM',
    haccpCompliant: true,
  },
  {
    id: 'pb-04',
    batchNumber: 'BATCH-2026-0927-D',
    recipeName: 'Artisan Baguettes & Focaccia',
    station: 'Bakery Ovens',
    plannedQty: 120,
    unit: 'loaves',
    status: 'Cooking',
    targetTempC: 220,
    currentTempC: 218.0,
    headChef: 'Baker Jean Moreau',
    startTime: '11:15 AM',
    estEndTime: '12:30 PM',
    haccpCompliant: true,
  },
];

export const MOCK_CONSUMPTION: ConsumptionLog[] = [
  {
    id: 'con-1',
    date: '2026-09-26',
    mealService: 'Dinner Service',
    plannedHeadcount: 480,
    actualHeadcount: 422,
    variancePercentage: -12.08,
    totalFoodPreparedKg: 288.0,
    totalConsumedKg: 242.5,
    unconsumedKg: 45.5,
    residualSurplusDivertedKg: 38.0,
    notes: 'Rainstorm reduced expected walk-in corporate banquet guests by ~12%. Surplus redirected to Hope Mission Shelter.',
  },
  {
    id: 'con-2',
    date: '2026-09-26',
    mealService: 'Lunch Service',
    plannedHeadcount: 650,
    actualHeadcount: 668,
    variancePercentage: 2.77,
    totalFoodPreparedKg: 390.0,
    totalConsumedKg: 384.0,
    unconsumedKg: 6.0,
    residualSurplusDivertedKg: 4.5,
    notes: 'Near zero waste profile. Remaining bread rolls given to evening staff.',
  },
  {
    id: 'con-3',
    date: '2026-09-25',
    mealService: 'Dinner Service',
    plannedHeadcount: 510,
    actualHeadcount: 460,
    variancePercentage: -9.8,
    totalFoodPreparedKg: 306.0,
    totalConsumedKg: 268.0,
    unconsumedKg: 38.0,
    residualSurplusDivertedKg: 32.0,
    notes: 'Post-conference dinner had 50 dropouts. Blast chilled and logged in Surplus Marketplace.',
  },
];

export const MOCK_WASTE_RECORDS: WasteRecord[] = [
  {
    id: 'wst-101',
    timestamp: '2026-09-27 11:30 AM',
    category: 'Preparation Trimmings',
    weightKg: 14.2,
    costUSD: 28.4,
    ghgKgCO2e: 35.5,
    department: 'Cold Prep Line 1',
    rootCause: 'Root vegetable peelings & broccoli stalk ends',
    loggedBy: 'Sous Chef Sarah Chen',
    epaHierarchyTier: 'Compost',
  },
  {
    id: 'wst-102',
    timestamp: '2026-09-26 09:15 PM',
    category: 'Plate Scraps',
    weightKg: 22.8,
    costUSD: 68.4,
    ghgKgCO2e: 57.0,
    department: 'Buffet Stations',
    rootCause: 'Oversized portion sizes on self-serve salad bar',
    loggedBy: 'Supervisor Liam Kelly',
    epaHierarchyTier: 'Compost',
  },
  {
    id: 'wst-103',
    timestamp: '2026-09-26 03:00 PM',
    category: 'Spoilage & Expiry',
    weightKg: 7.5,
    costUSD: 45.0,
    ghgKgCO2e: 18.75,
    department: 'Cold Storage Intake',
    rootCause: 'Ripened strawberries passed cosmetic threshold for banquet display',
    loggedBy: 'Receiving Officer Patel',
    epaHierarchyTier: 'Industrial Valorization',
  },
  {
    id: 'wst-104',
    timestamp: '2026-09-25 10:45 PM',
    category: 'Overproduction Surplus',
    weightKg: 31.0,
    costUSD: 140.0,
    ghgKgCO2e: 77.5,
    department: 'Main Kitchen',
    rootCause: 'Executive dining RSVP cancellation without 24hr notice',
    loggedBy: 'Executive Chef Vance',
    epaHierarchyTier: 'Feed Hungry People',
  },
];

export const MOCK_FORECAST_SERIES: ForecastPoint[] = [
  { date: 'Sep 21', dayName: 'Mon', historicalDemand: 580, predictedDemand: 570, lowerBound: 540, upperBound: 600, weather: 'Sunny 24°C', isHolidayOrEvent: false, confidenceScore: 0.92 },
  { date: 'Sep 22', dayName: 'Tue', historicalDemand: 610, predictedDemand: 605, lowerBound: 580, upperBound: 630, weather: 'Clear 22°C', isHolidayOrEvent: false, confidenceScore: 0.94 },
  { date: 'Sep 23', dayName: 'Wed', historicalDemand: 640, predictedDemand: 650, lowerBound: 620, upperBound: 680, weather: 'Rainy 18°C', isHolidayOrEvent: false, confidenceScore: 0.89 },
  { date: 'Sep 24', dayName: 'Thu', historicalDemand: 690, predictedDemand: 680, lowerBound: 650, upperBound: 710, weather: 'Sunny 24°C', isHolidayOrEvent: false, confidenceScore: 0.91 },
  { date: 'Sep 25', dayName: 'Fri', historicalDemand: 740, predictedDemand: 755, lowerBound: 720, upperBound: 790, weather: 'Clear 22°C', isHolidayOrEvent: true, eventDescription: 'Tech Summit Day 1', confidenceScore: 0.88 },
  { date: 'Sep 26', dayName: 'Sat', historicalDemand: 520, predictedDemand: 535, lowerBound: 500, upperBound: 570, weather: 'Rainy 18°C', isHolidayOrEvent: false, confidenceScore: 0.93 },
  { date: 'Sep 27 (Today)', dayName: 'Sun', historicalDemand: 490, predictedDemand: 485, lowerBound: 460, upperBound: 510, weather: 'Clear 22°C', isHolidayOrEvent: false, confidenceScore: 0.95 },
  { date: 'Sep 28', dayName: 'Mon', historicalDemand: 0, predictedDemand: 595, lowerBound: 560, upperBound: 630, weather: 'Sunny 24°C', isHolidayOrEvent: false, confidenceScore: 0.89 },
  { date: 'Sep 29', dayName: 'Tue', historicalDemand: 0, predictedDemand: 630, lowerBound: 590, upperBound: 670, weather: 'Clear 22°C', isHolidayOrEvent: false, confidenceScore: 0.87 },
  { date: 'Sep 30', dayName: 'Wed', historicalDemand: 0, predictedDemand: 680, lowerBound: 640, upperBound: 720, weather: 'Sunny 24°C', isHolidayOrEvent: true, eventDescription: 'End of Quarter All-Hands', confidenceScore: 0.85 },
  { date: 'Oct 01', dayName: 'Thu', historicalDemand: 0, predictedDemand: 710, lowerBound: 670, upperBound: 750, weather: 'Rainy 18°C', isHolidayOrEvent: false, confidenceScore: 0.86 },
  { date: 'Oct 02', dayName: 'Fri', historicalDemand: 0, predictedDemand: 760, lowerBound: 710, upperBound: 810, weather: 'Clear 22°C', isHolidayOrEvent: false, confidenceScore: 0.84 },
];

export const MOCK_OPTIMIZER_RECOMMENDATIONS: OptimizerRecommendation[] = [
  {
    id: 'opt-rec-1',
    menuDish: 'Mediterranean Lemon Herb Grilled Chicken',
    baselineDemandPortions: 480,
    recommendedBatchPortions: 425,
    variancePct: -11.45,
    safetyBufferPct: 6.5,
    expectedWasteReductionKg: 28.5,
    estimatedCostSavingsUSD: 232.0,
    confidenceScore: 0.94,
    rationale: 'XGBoost regression identifies 14% drop in Monday lunch foot-traffic following regional holiday weekend. Optimal stochastic buffer is 6.5%.',
    applied: false,
  },
  {
    id: 'opt-rec-2',
    menuDish: 'Wild Mushroom Risotto with White Truffle Oil',
    baselineDemandPortions: 220,
    recommendedBatchPortions: 195,
    variancePct: -11.36,
    safetyBufferPct: 5.0,
    expectedWasteReductionKg: 12.0,
    estimatedCostSavingsUSD: 165.0,
    confidenceScore: 0.91,
    rationale: 'High holding degradation rate (Arrhenius shelf life k=0.18). Reducing batch size prevents thermal breakdown.',
    applied: true,
  },
  {
    id: 'opt-rec-3',
    menuDish: 'Artisan Brioche Burger Buns',
    baselineDemandPortions: 320,
    recommendedBatchPortions: 280,
    variancePct: -12.5,
    safetyBufferPct: 8.0,
    expectedWasteReductionKg: 8.4,
    estimatedCostSavingsUSD: 72.0,
    confidenceScore: 0.88,
    rationale: 'Inventory lot LOT-2026-BUN-12 expires within 24h. Recommend baking smaller run and shifting diners to sandwich rolls.',
    applied: false,
  },
];

export const MOCK_RECIPIENTS: RecipientMatch[] = [
  {
    id: 'rec-01',
    recipientOrg: 'Downtown St. Jude Food Bank',
    facilityType: 'Food Bank',
    distanceKm: 3.4,
    transitTimeMins: 14,
    demandCapacityKg: 150.0,
    affinityScorePct: 98.4,
    coldStorageAvailable: true,
    dietaryMatch: true,
    contactPerson: 'Maria Rodriguez',
    contactPhone: '+1 (555) 234-8901',
    status: 'Pending Match',
  },
  {
    id: 'rec-02',
    recipientOrg: 'Hope Mission Family Shelter',
    facilityType: 'Homeless Shelter',
    distanceKm: 5.8,
    transitTimeMins: 22,
    demandCapacityKg: 80.0,
    affinityScorePct: 94.2,
    coldStorageAvailable: true,
    dietaryMatch: true,
    contactPerson: 'Rev. Thomas Bailey',
    contactPhone: '+1 (555) 345-6789',
    status: 'Assigned',
  },
  {
    id: 'rec-03',
    recipientOrg: 'Covenant Youth Haven',
    facilityType: 'Youth Refuge',
    distanceKm: 7.2,
    transitTimeMins: 28,
    demandCapacityKg: 45.0,
    affinityScorePct: 88.7,
    coldStorageAvailable: false,
    dietaryMatch: false,
    contactPerson: 'Jessica Sterling',
    contactPhone: '+1 (555) 456-7890',
    status: 'Pending Match',
  },
];

export const MOCK_DONATION_MANIFEST: DonationManifest = {
  manifestId: 'MNF-2026-0927-088',
  trackingNumber: 'TRK-FL-89412-CA',
  donorOrg: 'Grand Hyatt Culinary Center (Kitchen #04)',
  recipientOrg: 'Downtown St. Jude Food Bank',
  totalWeightKg: 42.5,
  mealPortions: 85,
  category: 'Cooked Entrees & Roasted Proteins',
  storageTemp: 'Chilled (3.2°C maintained)',
  transitTemperatureC: 3.4,
  departureTime: '11:45 AM',
  estimatedArrival: '12:15 PM',
  courierDriver: 'Alex Mercer (EV Van #03)',
  vehiclePlate: '7XFL492',
  status: 'In Transit',
  haccpCheckPassed: true,
  digitalSignatures: {
    donorSigned: true,
    courierSigned: true,
    recipientSigned: false,
  },
};

export const MOCK_DRIVER_WAYPOINTS: DriverWaypoint[] = [
  {
    id: 'wp-1',
    type: 'Depot',
    name: 'FoodLoop Regional Courier Depot',
    address: '100 Logistics Way, Bay 4',
    timeWindow: '10:00 - 10:15 AM',
    cargoWeightKg: 0,
    completed: true,
    temperatureTargetC: 'Pre-cooled 2°C',
    notes: 'Vehicle inspected, digital thermometer calibrated',
  },
  {
    id: 'wp-2',
    type: 'Pickup',
    name: 'Grand Hyatt Culinary Center',
    address: '500 Grand Ave, Loading Dock B',
    timeWindow: '11:30 - 11:45 AM',
    cargoWeightKg: 42.5,
    completed: true,
    temperatureTargetC: 'Chilled 3.2°C',
    notes: 'Pickup 85 portions Mediterranean Chicken. Handover QR verified.',
  },
  {
    id: 'wp-3',
    type: 'Dropoff',
    name: 'Downtown St. Jude Food Bank',
    address: '812 Mission Blvd, Service Entry',
    timeWindow: '12:05 - 12:20 PM',
    cargoWeightKg: 42.5,
    completed: false,
    temperatureTargetC: 'Chilled < 4.0°C',
    notes: 'Unload into Walk-in Chiller #2. Recipient signature required.',
  },
  {
    id: 'wp-4',
    type: 'Pickup',
    name: 'Harvest Boulangerie & Cafe',
    address: '320 Artisan Row',
    timeWindow: '12:45 - 01:00 PM',
    cargoWeightKg: 28.0,
    completed: false,
    temperatureTargetC: 'Dry Ambient 18°C',
    notes: 'Pick up 60 loaves surplus baguettes & sourdough.',
  },
  {
    id: 'wp-5',
    type: 'Dropoff',
    name: 'Hope Mission Family Shelter',
    address: '1440 Hope St',
    timeWindow: '01:20 - 01:40 PM',
    cargoWeightKg: 28.0,
    completed: false,
    temperatureTargetC: 'Dry Ambient',
    notes: 'Deliver bakery surplus for evening dinner line.',
  },
];

export const MOCK_KNOWLEDGE_BASE: KnowledgeArticle[] = [
  {
    id: 'rag-01',
    title: 'FDA Food Code Section 3-501.19: Time as a Public Health Control (4-Hour Rule)',
    source: 'FDA Food Code 2022',
    category: 'Food Safety',
    excerpt: 'Ready-to-eat potentially hazardous food removed from temperature control must be cooked and served, served at any temperature, or discarded within 4 hours.',
    fullContent: 'Under the 2022 FDA Food Code, food that is held without temperature control must be clearly marked with the time of removal and the 4-hour discard threshold. If the food temperature exceeds 70°F (21°C) during warm ambient conditions, maximum allowable holding time is 6 hours only if initial temperature was ≤41°F (5°C) and temperature never exceeds 70°F. In the FoodLoop AI system, any food marked as surplus must possess an immutable timestamp from blast chiller extraction.',
    keyRule: 'Critical Limit: ≤4 hours for ambient holding; ≤6 hours if monitored continuously below 21°C.',
    lastUpdated: 'Updated Jan 2024',
  },
  {
    id: 'rag-02',
    title: 'Bill Emerson Good Samaritan Food Donation Act (42 U.S. Code § 1791)',
    source: 'Bill Emerson Good Samaritan Act',
    category: 'Legal & Liability',
    excerpt: 'Protects food donors and nonprofit distribution agencies from civil and criminal liability arising from the nature, age, packaging, or condition of apparently wholesome food.',
    fullContent: 'Signed into federal law to encourage food donation, the Act shields restaurants, institutional kitchens, grocery stores, and food processors from liability unless the injury was caused by gross negligence or intentional misconduct. Donors utilizing certified cold-chain tracking systems (like FoodLoop AI digital manifests) demonstrate due diligence and good-faith adherence to safety standards.',
    keyRule: 'Exemption from liability applies when food is apparently wholesome and donated in good faith.',
    lastUpdated: 'Reauthorized 2023',
  },
  {
    id: 'rag-03',
    title: 'HACCP Principle 3: Establishing Critical Limits for Cooling Hot Surplus Foods',
    source: 'HACCP Standard',
    category: 'Food Safety',
    excerpt: 'Hot cooked food must cool from 135°F (57°C) to 70°F (21°C) within 2 hours, and from 70°F to 41°F (5°C) or lower within an additional 4 hours (total 6 hours).',
    fullContent: 'The two-stage cooling procedure is essential for pathogen prevention, specifically Bacillus cereus and Clostridium perfringens sporulation. Rapid blast chilling or ice-bath immersion is mandatory prior to vacuum-sealed packaging for redistribution.',
    keyRule: 'Two-stage cool: 57°C to 21°C in ≤2h; 21°C to 5°C in ≤4h.',
    lastUpdated: 'ISO 22000 Harmonized',
  },
  {
    id: 'rag-04',
    title: 'Cold Chain Courier SOP: In-Transit Temperature Telemetry Verification',
    source: 'Cold Chain SOP',
    category: 'Logistics',
    excerpt: 'Refrigerated couriers must maintain active payload temperature monitoring between 0°C and 4.4°C. Excursions above 5°C for >30 minutes trigger immediate quarantine.',
    fullContent: 'FoodLoop drivers are equipped with BLE continuous temperature dataloggers. If the ambient chamber breaches 4.4°C for over 30 minutes, the manifest changes to Quarantine status and routing redirects to an emergency blast-chill hub.',
    keyRule: 'Cold Chain Tolerance: 0°C - 4.4°C. Max excursion: 30 minutes.',
    lastUpdated: 'Revised Aug 2026',
  },
];

export const MOCK_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'notif-1',
    title: 'Critical Expiry Alert: Atlantic Salmon (18.5 kg)',
    message: 'LOT-2026-SLM-09 expires in 22 hours. Post surplus or schedule immediate menu incorporation.',
    timestamp: '10 mins ago',
    category: 'urgent',
    read: false,
    actionTarget: 'inventory',
  },
  {
    id: 'notif-2',
    title: 'Driver Handover Imminent: TRK-FL-89412-CA',
    message: 'Courier Alex Mercer is 1.2 km away from Downtown St. Jude Food Bank. Prepare recipient QR receiver.',
    timestamp: '25 mins ago',
    category: 'logistics',
    read: false,
    actionTarget: 'qr_verification',
  },
  {
    id: 'notif-3',
    title: 'New AI Forecast Recommendation',
    message: 'XGBoost engine recommends reducing Mediterranean Chicken batch size by 55 portions (-11.4%).',
    timestamp: '1 hour ago',
    category: 'production',
    read: false,
    actionTarget: 'production_optimizer',
  },
  {
    id: 'notif-4',
    title: 'HACCP Audit Log Cryptographically Signed',
    message: 'Daily temperature telemetry batch for walk-in chiller #3 sealed to immutable audit ledger.',
    timestamp: '3 hours ago',
    category: 'audit',
    read: true,
    actionTarget: 'audit_logs',
  },
  {
    id: 'notif-5',
    title: 'Weekly EPA Waste Diverted Milestone',
    message: 'Kitchen #04 achieved 91.2% food recovery diversion this week! 1,480 kg diverted from landfill.',
    timestamp: 'Yesterday',
    category: 'system',
    read: true,
    actionTarget: 'impact_dashboard',
  },
];

export const MOCK_AUDIT_LOGS: AuditLogEntry[] = [
  {
    id: 'aud-9901',
    timestamp: '2026-09-27 11:46:12 UTC',
    actor: 'Chef Marcus Vance',
    role: 'Kitchen Manager',
    action: 'DECLARE_SURPLUS_BROADCAST',
    entity: 'FoodListing::lst-48921 (42.5 kg Chicken)',
    ipAddress: '192.168.1.104',
    sha256Hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    severity: 'low',
  },
  {
    id: 'aud-9902',
    timestamp: '2026-09-27 11:47:05 UTC',
    actor: 'Courier Alex Mercer',
    role: 'Logistics Courier',
    action: 'VERIFY_HMAC_HANDOVER_QR',
    entity: 'RescueClaim::clm-10294 (Donor to Courier)',
    ipAddress: '172.56.21.89',
    sha256Hash: 'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e',
    severity: 'medium',
  },
  {
    id: 'aud-9903',
    timestamp: '2026-09-27 10:30:00 UTC',
    actor: 'System AI Engine (OR-Tools)',
    role: 'System Daemon',
    action: 'RUN_DISPATCH_CVRPTW_SOLVER',
    entity: 'RoutingCluster::grid-zone-north',
    ipAddress: '127.0.0.1 (Internal Service)',
    sha256Hash: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    severity: 'low',
  },
  {
    id: 'aud-9904',
    timestamp: '2026-09-27 09:15:33 UTC',
    actor: 'Quality Auditor Helena Brandt',
    role: 'Safety Auditor',
    action: 'OVERRIDE_TEMPERATURE_STATUS',
    entity: 'Batch::BATCH-2026-0927-A (Passed manual probe calibration)',
    ipAddress: '192.168.1.182',
    sha256Hash: '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a',
    severity: 'high',
  },
  {
    id: 'aud-9905',
    timestamp: '2026-09-26 18:22:19 UTC',
    actor: 'Super Admin Eleanor Vance',
    role: 'Super Admin',
    action: 'UPDATE_ORGANIZATION_SETTINGS',
    entity: 'TenantConfig::GrandHyattCulinary',
    ipAddress: '24.120.88.14',
    sha256Hash: 'ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d',
    severity: 'medium',
  },
];
