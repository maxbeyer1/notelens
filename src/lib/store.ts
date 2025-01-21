import { load, Store } from "@tauri-apps/plugin-store";

// Store configuration
const STORE_NAME = "notelens.json";

// Type for our store values
export interface StoreValues {
  onboarding_complete: boolean;
  // Add other store values here as needed
}

// Initial values for store
const INITIAL_VALUES: StoreValues = {
  onboarding_complete: false,
};

// Store singleton
let storePromise: Promise<Store> | null = null;

// Initialize store
const getStore = async () => {
  if (!storePromise) {
    storePromise = load(STORE_NAME, { autoSave: true });
    const store = await storePromise;

    // Initialize any missing values
    for (const [key, value] of Object.entries(INITIAL_VALUES) as [
      keyof StoreValues,
      StoreValues[keyof StoreValues],
    ][]) {
      const existing = await store.get(key);
      if (existing === undefined) {
        await store.set(key, value);
        console.log(`Initialized store value: ${key} = ${value}`);
      }
    }

    // Save store to file
    await store.save();
  }
  return storePromise;
};

export const store = {
  async get<T>(key: keyof StoreValues): Promise<T | null> {
    const store = await getStore();
    return store.get<T>(key) as Promise<T | null>;
  },

  async set<T>(key: keyof StoreValues, value: T): Promise<void> {
    const store = await getStore();
    await store.set(key, value);
  },

  async save(): Promise<void> {
    const store = await getStore();
    await store.save();
  },
};
