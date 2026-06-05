export interface PlanRequest {
  origin: string;
  destination: string;
  budget: number;
  intercity_mode: TravelMode;
  city_transit: CityTransit;
  days: number;
  preferences: Preference[];
  start_date: string;
}

export type TravelMode = 'high_speed_rail' | 'flight' | 'self_drive' | 'bus' | 'train';
export type CityTransit = 'public_transit' | 'taxi' | 'rental_car' | 'walking' | 'mixed';
export type Preference = 'nature' | 'history' | 'food' | 'family';

export type TaskStatus =
  | 'pending'
  | 'running'
  | 'attractions_done'
  | 'weather_done'
  | 'hotels_done'
  | 'planning'
  | 'completed'
  | 'failed';

export interface PlanResponse {
  task_id: string;
  status: TaskStatus;
  created_at: string;
}

export interface RouteCoordinate {
  lng: number;
  lat: number;
  name: string;
  type: 'attraction' | 'hotel' | 'restaurant';
  order: number;
}

export interface AttractionItem {
  name: string;
  lng: number;
  lat: number;
  duration: string;
  ticket: number;
  time_slot: string;
  rating?: number;
  category?: string;
  order: number;
}

export interface HotelItem {
  name: string;
  lng: number;
  lat: number;
  price: number;
  rating?: number;
  address?: string;
}

export interface MealItem {
  type: 'breakfast' | 'lunch' | 'dinner';
  suggestion: string;
  estimated_cost: number;
}

export interface TransportItem {
  from: string;
  to: string;
  mode: string;
  cost: number;
}

export interface DailyPlan {
  day: number;
  date: string;
  weather?: {
    day_weather: string;
    night_weather: string;
    high_temp: number;
    low_temp: number;
    wind?: string;
    clothing_advice?: string;
    travel_advice?: string;
  };
  attractions: AttractionItem[];
  hotel: HotelItem | null;
  meals: MealItem[];
  transport: TransportItem[];
  daily_cost: number;
  route_coordinates: RouteCoordinate[];
}

export interface TierPlan {
  daily_plans: DailyPlan[];
  total_cost: number;
  budget_usage: number;
}

export interface PlanResult {
  task_id: string;
  input: PlanRequest;
  weather: Array<Record<string, unknown>>;
  plans: {
    economy: TierPlan;
    comfort: TierPlan;
    luxury: TierPlan;
  };
}

export type TierKey = 'economy' | 'comfort' | 'luxury';

export interface SSEEvent {
  event: string;
  agent?: string;
  message?: string;
  data?: Record<string, unknown>;
  timestamp: string;
}

export const TRAVEL_MODE_LABELS: Record<TravelMode, string> = {
  high_speed_rail: '高铁',
  flight: '飞机',
  self_drive: '自驾',
  bus: '大巴',
  train: '火车',
};

export const CITY_TRANSIT_LABELS: Record<CityTransit, string> = {
  public_transit: '公交/地铁',
  taxi: '打车',
  rental_car: '租车',
  walking: '步行',
  mixed: '打车+地铁',
};

export const PREFERENCE_LABELS: Record<Preference, string> = {
  nature: '🏔 自然风光',
  history: '🏛 历史文化',
  food: '🍜 美食购物',
  family: '👨‍👩‍👧 亲子休闲',
};

export const TIER_LABELS: Record<TierKey, string> = {
  economy: '经济',
  comfort: '舒适',
  luxury: '豪华',
};
