
-- Drop old plans table if exists
DROP TABLE IF EXISTS plans;

-- Create plans table
CREATE TABLE plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    condition_combo TEXT,
    morning TEXT,
    afternoon TEXT,
    evening TEXT,
    night TEXT,
    exercises TEXT
);

-- ✅ Insert diet + exercise plans

INSERT INTO plans (condition_combo, morning, afternoon, evening, night, exercises) VALUES
('overweight,thyroid,sugar',
 'Oats with almond milk and chia seeds',
 'Brown rice, dal, steamed broccoli, grilled chicken/fish',
 'Green tea with handful of nuts',
 'Vegetable soup with multigrain roti and paneer curry',
 '30 mins walking, yoga (surya namaskar), light strength training');

INSERT INTO plans (condition_combo, overweight, sugar',
 'Boiled eggs or sprouts with green tea',
 'Quinoa with mixed veggies and dal',
 'Fruit salad with flax seeds',
 'Vegetable khichdi with curd',
 'Cardio (cycling/jogging 20 mins), yoga (pranayama)');

INSERT INTO plans (condition_combo, underweight',
 'Banana milkshake with oats',
 'Rice with chicken curry and salad',
 'Peanut butter sandwich',
 'Paneer butter masala with 2 rotis',
 'Weight training, push-ups, resistance exercises');

INSERT INTO plans (condition_combo, thyroid',
 'Ragi dosa with chutney',
 'Millet khichdi with sambar',
 'Fruit smoothie',
 'Vegetable pulao with curd',
 'Breathing yoga, light jogging, meditation');

INSERT INTO plans (condition_combo, pcod',
 'Vegetable poha with sprouts',
 'Brown rice with dal and spinach sabzi',
 'Green tea with almonds',
 'Soup with multigrain roti and soya curry',
 'Yoga for PCOD, stretching, brisk walk');

INSERT INTO plans (condition_combo, sugar',
 'Oats with cinnamon and apple slices',
 'Chapati with sabzi and dal',
 'Carrot sticks and hummus',
 'Vegetable upma with sprouts',
 'Walking after meals, yoga, cycling');

INSERT INTO plans (condition_combo, bp',
 'Fruit bowl (papaya, apple, watermelon)',
 'Steamed veggies with brown rice',
 'Green tea',
 'Moong dal khichdi with spinach',
 'Breathing exercises, yoga, walking');

INSERT INTO plans (condition_combo, overweight',
 'Upma with vegetables',
 'Brown rice + rajma + salad',
 'Buttermilk with cucumber',
 'Vegetable soup + roti + sabzi',
 'Skipping rope, HIIT, brisk walk');

INSERT INTO plans (condition_combo, underweight,pcod',
 'Banana shake + boiled eggs',
 'Rice + dal + potato curry',
 'Dry fruits and milk',
 'Paneer curry + roti + salad',
 'Strength training, yoga, resistance bands');

INSERT INTO plans (condition_combo, normal',
 'Idli + sambar',
 'Rice + dal + 2 rotis + sabzi',
 'Fruit salad',
 'Vegetable curry + 2 rotis',
 'Yoga + 20 min jogging');
