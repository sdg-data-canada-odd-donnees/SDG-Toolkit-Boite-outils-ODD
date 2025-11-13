# Starburst chart
# R script to create a starburst chart showing the progress status of SDG indicators
# For each indicator, a line segment indicates the direction and relative degree of progress.
# Line segments radiating outwards from the zero-axis indicate progress, with longer lines indicating more progress.
# Line segments radiating inwards from the zero-axis indicate deterioration.
# Indicators that have achieved their target are designated with a star symbol.
# When >= 60% of indicators within a goal are reporting a progress status, an average level of progress across the goal is indicated by a dashed line.

library(tidyverse)
library(yaml)
library(here)
library(ggstar)

# fetch indicator_calculation_components.yml file
src <- here("progress", "tests", "indicator_calculation_components_gif_master_sep16-2025.yml")

# Read progress outputs from indicator calculation components file
progress_calc_components <- read_yaml(src)

# create empty tibble to append progress statuses to
progress_status_by_indicator <- tibble()
# Append each indicator and its progress status (from indicator_calculation_components.yml)
for (indicator_id in names(progress_calc_components)) {
  indicator_progress <- tibble(
    ind = indicator_id,
    progress_status = progress_calc_components[[indicator_id]][["progress_status"]],
    progress_score = progress_calc_components[[indicator_id]][["score"]]
  )
  progress_status_by_indicator <- bind_rows(progress_status_by_indicator, indicator_progress)
}

# Convert all empty and unavailable progress statuses to not_available
# also set the score to 5 everywhere where the target is achieved
progress_status_by_indicator <- progress_status_by_indicator %>%
  mutate(
    progress_status = case_when(
      progress_status %in% c("", "not_available_manual") ~ "not_available",
      .default = progress_status
    ),
    progress_score = case_when(
      progress_status == "target_achieved" ~ 5,
      .default = progress_score
    )
  )

labels <- c(
  "substantial_deterioration", # remove
  "deterioration",
  "moderate_deterioration", # remove
  "limited_progress",
  "moderate_progress",
  "substantial_progress",
  "target_achieved"
)

# create table of progress labels and corresponding imposed y-axis values
progress_concordance <-
  tibble(
    label = factor(labels, levels = labels),
    value = c(-3, -2, -1, 0.5, 1.5, 2.5, 3.5)
  )

# create vector of goal labels (to sort factor)
goals <- paste0("Goal", 1:17)

# transform progress_status_by_indicator to dataframe for ggplot
statuses <- progress_status_by_indicator %>%
  select(indicator = ind, label = progress_status, score = progress_score) %>%
  mutate(
    indicator = str_replace_all(indicator, "-", "."),
    label = recode(label, significant_deterioration = "substantial_deterioration")
  ) %>%
  left_join(progress_concordance) %>%
  mutate(
    goal = str_extract(indicator, "^[0-9]+"),
    target = str_extract(indicator, "^[0-9]+\\.[0-9]+"),
    goal = paste0("Goal", goal),
    goal = factor(goal, levels = goals)
    # indicator_id = factor(row_number())
  ) %>%
  arrange(goal, indicator) %>%
  mutate(
    indicator_id = row_number()
  )

# goal data for creating frames around wheel
goal_data <- statuses %>%
  group_by(goal) %>%
  summarise(min_ind = min(indicator_id), max_ind = max(indicator_id))

# Get the goals whose progress is below 60% reported
not_above_60_pct_reported <-
  statuses %>%
  group_by(goal) %>%
  count(label) %>%
  mutate(total = sum(n)) %>%
  filter(label == "not_available") %>%
  mutate(pct = n / total) %>%
  filter(pct > 0.4)

# Calculate the avg goal score
goal_progress <- statuses %>%
  filter(!(goal %in% not_above_60_pct_reported$goal)) %>%
  group_by(goal) %>%
  summarise(goal_score = mean(score, na.rm = TRUE)) %>%
  mutate(label = case_when(
    # Add something to deal with goals that are all target_achieved
    goal_score >= 2.5 ~ "substantial_progress",
    goal_score < 2.5 & goal_score >= 0 ~ "moderate_progress",
    goal_score < 0 & goal_score >= -2.5 ~ "limited_progress",
    goal_score < -2.5 ~ "deterioration"
  )) %>%
  left_join(progress_concordance) %>%
  left_join(goal_data)

# specify sdg colours for ggplot palette
sdg_palette <- c(
  Goal1  = "#E5263B",
  Goal2  = "#DDA83A",
  Goal3  = "#4D9F38",
  Goal4  = "#C5192D",
  Goal5  = "#FE3A21",
  Goal6  = "#26BDE2",
  Goal7  = "#FCC30E",
  Goal8  = "#A21A42",
  Goal9  = "#FD6A26",
  Goal10 = "#E11584",
  Goal11 = "#FD9D25",
  Goal12 = "#BF8B2E",
  Goal13 = "#3F7E44",
  Goal14 = "#0997D9",
  Goal15 = "#55C02A",
  Goal16 = "#01689D",
  Goal17 = "#19486A"
)


ggplot(statuses, aes(indicator_id, value)) +
  geom_segment(
    data = goal_progress,
    aes(
      x = min_ind, xend = max_ind,
      y = value, yend = value,
      color = goal
    ),
    lty = "33"
  ) +
  geom_segment( # bars indicating progress value
    aes(
      x = indicator_id, xend = indicator_id,
      y = 0, yend = value,
      color = goal
    ),
    size = 1.1
  ) +
  geom_hline( # grey axis line
    yintercept = 0,
    size = 2,
    color = "grey"
  ) +
  geom_segment( # axis ticks indicating no progress calculated
    data = statuses %>% filter(is.na(value)),
    aes(
      x = indicator_id, xend = indicator_id,
      y = -0.15, yend = 0.15,
      color = goal
    ),
    size = 0.5
  ) +
  geom_point( # points on progress lines
    aes(
      x = ifelse(value != 3.5, indicator_id, NA),
      y = ifelse(value != 3.5, value, NA),
      color = goal
    ),
    size = 2.5
  ) +
  geom_star( # stars indicating achieved indicators
    aes(
      x = ifelse(value == 3.5, indicator_id, NA),
      y = ifelse(value == 3.5, value, NA),
      color = goal,
      fill = goal,
      angle = 360 * (indicator_id - 1) / nrow(statuses)
    ),
    size = 2.5
  ) +
  geom_rect( # goal frames
    data = goal_data,
    aes(xmin = min_ind, xmax = max_ind, ymin = 4.1, ymax = 5.5, fill = goal),
    inherit.aes = FALSE
  ) +
  scale_color_manual( # goal color
    values = sdg_palette,
    guide = guide_none()
  ) +
  scale_fill_manual( # goal fill
    values = sdg_palette,
    guide = guide_none()
  ) +
  coord_polar(clip = "off") +
  xlim(c(1, nrow(statuses) + 1)) +
  ylim(c(-6, 5.5)) +
  theme_void()

ggsave(here("progress", "imgs", "starbust_chart.png"), height = 10, width = 10)

# legend ------------------------------------------------------------------

legend_segment <-
  statuses %>%
  distinct(label, value) %>%
  mutate(value = replace_na(value, 0.15)) %>%
  arrange(value) %>%
  mutate(x = row_number(), ystart = ifelse(label == "not_available", -0.15, 0))

legend_segment %>%
  ggplot() +
  geom_segment(
    data = legend_segment %>% filter(label != "not_available"),
    aes(x = x, xend = x, y = ystart, yend = value), size = 1.1
  ) +
  geom_hline(yintercept = 0, size = 2, color = "grey80") +
  geom_point(
    data = legend_segment %>% filter(!(label %in% c("not_available", "target_achieved"))),
    aes(x = x, y = value), size = 2.5
  ) +
  geom_star(
    data = legend_segment %>% filter(label == "target_achieved"),
    aes(
      x = x,
      y = value,
      # angle = 360 * x / 75
    ),
    size = 2.5,
    fill = "black"
  ) +
  geom_segment(
    data = legend_segment %>% filter(label == "not_available"),
    aes(x = x, xend = x, y = ystart, yend = value), size = 0.5
  ) +
  xlim(c(0, 8)) +
  ylim(c(-6, 5.5)) +
  # coord_polar(clip = "off") +
  theme_void()

ggsave(here("progress", "imgs", "starburst_legend.png"), height = 5)
