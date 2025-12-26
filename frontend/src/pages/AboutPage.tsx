export const AboutPage = () => {
  return (
    <div className="Card space-y-8">
      <section>
        <h2 className="Headline text-2xl mb-4">About Portion Note</h2>
        <p className="text-Ink/80 leading-relaxed">
          Portion Note helps you track your meals and steps with minimal effort. 
          Log your food, monitor your nutrition targets, and get smart suggestions powered by AI.
        </p>
      </section>

      <section>
        <h3 className="font-semibold text-lg mb-3">Getting Started</h3>
        <div className="space-y-4 text-Ink/80">
          <div>
            <h4 className="font-medium text-Ink mb-1">Adding Foods</h4>
            <p className="text-sm leading-relaxed">
              Go to <strong>Foods</strong> and tap "Add Food". Start typing a food name and you'll see Australian food suggestions. 
              Select one and the nutrition values will automatically populate using AI. You can also manually enter nutrition details if needed.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">Logging Meals</h4>
            <p className="text-sm leading-relaxed">
              On the <strong>Today</strong> page, tap any meal section (Breakfast, Lunch, Dinner, or Snacks) to add food items. 
              Select from your food library, adjust the quantity, and your daily totals will update automatically.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">Tracking Steps</h4>
            <p className="text-sm leading-relaxed">
              Enter your daily steps on the <strong>Today</strong> page. Steps are converted to calories burned 
              (default: 0.04 kcal per step) which adjusts your remaining calorie budget.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">Viewing Progress</h4>
            <p className="text-sm leading-relaxed">
              Check <strong>History</strong> to see your weekly summaries, including average calories, protein, and steps. 
              View charts and trends to understand your eating patterns.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">Adjusting Settings</h4>
            <p className="text-sm leading-relaxed">
              In <strong>Settings</strong>, customize your daily calorie target, protein range, and step calorie factor. 
              You can also enable or disable nutrition tracking for fibre, carbs, fat, sugar, and sodium.
            </p>
          </div>
        </div>
      </section>

      <section>
        <h3 className="font-semibold text-lg mb-3">AI Features</h3>
        <div className="space-y-4 text-sm">
          <div>
            <h4 className="font-medium text-Ink mb-1">What is the autocomplete feature?</h4>
            <p className="text-Ink/80 leading-relaxed">
              When adding foods, type 2-3 letters and you'll see suggestions for Australian brands and products 
              (like Tim Tams, Vegemite, Arnott's). This makes it faster to find common foods without typing full names.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">How does AI populate nutrition data?</h4>
            <p className="text-Ink/80 leading-relaxed">
              When you select an autocomplete suggestion, AI looks up the nutrition information (calories, protein, fibre, carbs, fat, sugar, sodium) 
              and fills it in automatically. You'll see "✨ Nutrition values populated by AI" when this happens.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">Is the AI nutrition data accurate?</h4>
            <p className="text-Ink/80 leading-relaxed">
              AI nutrition data is generally reliable but may not always match packaging exactly. 
              You can always edit the values manually if you have more precise information.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">What are AI suggestions?</h4>
            <p className="text-Ink/80 leading-relaxed">
              The app can provide personalized suggestions based on your eating patterns, like reminders for protein intake, 
              balanced meal planning, or identifying repeated high-calorie snacks. These appear on your Today page when relevant.
            </p>
          </div>
        </div>
      </section>

      <section>
        <h3 className="font-semibold text-lg mb-3">Additional Features</h3>
        <div className="space-y-4 text-sm">
          <div>
            <h4 className="font-medium text-Ink mb-1">Favourites</h4>
            <p className="text-Ink/80 leading-relaxed">
              Mark foods as favourites (⭐) to quickly find them in your food library. 
              Favourites appear at the top of the list for faster meal logging.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">Meal Templates</h4>
            <p className="text-Ink/80 leading-relaxed">
              Save common meals (like your usual breakfast) as templates. 
              Quickly add all items at once instead of selecting them individually every day.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">Weekly Insights</h4>
            <p className="text-Ink/80 leading-relaxed">
              View your weekly averages for calories, protein, steps, and net calories. 
              See which days you met your targets and identify patterns in your nutrition habits.
            </p>
          </div>
          
          <div>
            <h4 className="font-medium text-Ink mb-1">Custom Nutrition Tracking</h4>
            <p className="text-Ink/80 leading-relaxed">
              Track more than just calories and protein. Enable tracking for fibre, carbs, fat, saturated fat, sugar, 
              and sodium in Settings. Set custom targets for each nutrient.
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-Ink/10 pt-6">
        <p className="text-xs text-Ink/60 text-center">
          Portion Note v1.0 • Mobile-first meal and step tracker
        </p>
      </section>
    </div>
  );
};
