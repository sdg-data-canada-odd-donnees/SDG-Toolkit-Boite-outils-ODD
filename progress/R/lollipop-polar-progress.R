# Polar lollipop chart
library(tidyverse)
library(here)
library(yaml)
# library(ggforce)

# Update src with the path to the indicator_calculation_components.yml file that contains the relevant progress data
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
  "deterioration",
  "limited_progress",
  "moderate_progress",
  "substantial_progress",
  "target_achieved"
)

# create table of progress labels and corresponding imposed y-axis values
progress_concordance <-
  tibble(
    label = factor(labels, levels = labels),
    value = c(-2, 0.5, 1.5, 2.5, 3.5)
  )

goals <- paste0("Goal", 1:17)

statuses <- progress_status_by_indicator %>%
  select(indicator = ind, label = progress_status) %>%
  mutate(
    indicator = str_replace_all(indicator, "-", "."),
    label = recode(label, significant_deterioration = "substantial_deterioration")
  ) %>%
  left_join(progress_concordance) %>%
  mutate(
    goal = str_extract(indicator, "^[0-9]+"),
    goal_no = as.numeric(goal),
    target = str_extract(indicator, "^[0-9]+\\.[0-9]+"),
    goal = factor(paste0("Goal", goal), levels = goals),
    indicator_id = factor(row_number()),
    label = factor(label, levels = labels)
  ) %>%
  group_by(goal, goal_no, label, value) %>%
  count(value, name = "count") %>%
  na.omit()

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

# plot with no legend & no NA count ------------------------------------------

# Point size correlates with count of indicators in each status per goal
statuses %>%
  ggplot() +
  geom_vline(xintercept = 0, color = "grey80", size = 2) +
  # geom_segment(
  #   aes(x = -3, xend = 3, y = 0.25, yend = 0.25)
  # ) +
  geom_segment(
    data = statuses %>%
      group_by(goal, goal_no) %>%
      summarise(value_min = min(value), value_max = max(value)),
    aes(x = value_min, xend = value_max, y = goal_no, yend = goal_no),
    color = "black"
  ) +
  geom_point(
    aes(
      x = value, y = goal_no,
      color = goal, size = count
    )
  ) +
  geom_text(
    data = statuses %>% distinct(goal_no, goal),
    aes(
      x = 5, y = goal_no,
      label = goal
    ),
    size = 2
  ) +
  scale_size(
    range = c(2, 6),
    name = "Number of indicators"
  ) +
  scale_fill_manual(
    values = sdg_palette,
    guide = guide_none()
  ) +
  scale_color_manual(
    values = sdg_palette,
    guide = guide_none()
  ) +
  coord_polar(theta = "y", clip = "off", start = -0.1) +
  xlim(c(-6, 6)) +
  ylim(c(0.25, 17.25)) +
  theme_void() +
  theme(
    legend.position = "bottom"
    # axis.text.x = element_text(color = "black")
  )

ggsave(here("progress", "imgs", "lollipop-progress-polar.png"), height = 8, width = 8)


# legend ------------------------------------------------------------------

legend_segment <-
  statuses %>%
  filter(!is.na(value)) %>%
  distinct(label, value) %>%
  summarise(min_y = min(value), max_y = max(value))

statuses %>%
  distinct(label, value) %>%
  ggplot() +
  geom_curve(
    aes(x = -1, xend = 1, y = -0.25, yend = -0.25),
    size = 2, color = "grey80", curvature = -0.175
  ) +
  geom_segment(
    data = legend_segment,
    aes(x = 0, xend = 0, y = min_y, yend = max_y)
  ) +
  geom_point(
    aes(x = 0, y = value),
    size = 3
  ) +
  xlim(c(-6, 6)) +
  ylim(c(-6, 6)) +
  theme_void()

ggsave(here("progress", "imgs", "polar-lollipop", "legend.png"))
