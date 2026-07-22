# Recommended Presentation Story Flow

1. Start with the honest framing.
   - This is a demand-first project with revenue as a downstream planning layer.
   - The attendance model is noisy but useful.
   - The raw revenue-proxy fit looks strong because stage pricing is embedded in the target.

2. Show the scorecard fast.
   - XGBoost is the best attendance model.
   - Tree models beat the linear baseline.
   - The high revenue-proxy R2 is not the headline claim.

3. Make the model-selection decision explicit.
   - Primary feature-discovery model: attendance_equivalent_after_price_removal.
   - Supporting bridge: revenue_proxy_no_stage_feature.
   - Appendix diagnostic: revenue_proxy_full.

4. Explain the real drivers.
   - Team strength
   - Recent form
   - Team identity
   - Venue / market context
   - Match competitiveness

5. Explain what is weak or contaminated.
   - stage_detail is mechanical in the full revenue-proxy setup.
   - stadium and city are proxy variables because explicit capacity / market fields are missing.
   - calendar variables are weak.

6. Then show stage economics as scenario context, not causal discovery.
   - Group baseline
   - Round of 16 step-up
   - Quarter-final / semi-final / final premium ladder

7. Close with management language.
   - The project is useful now as a planning and scenario tool.
   - It is not yet a production-grade causal revenue engine.
   - The next upgrade is explicit capacity + market fields and local North American attendance rows.
