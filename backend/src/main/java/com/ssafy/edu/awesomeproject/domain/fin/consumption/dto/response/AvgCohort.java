package com.ssafy.edu.awesomeproject.domain.fin.consumption.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AvgCohort(
    @JsonProperty("cohort") Long cohort,
    @JsonProperty("avg_save_box") double avgSaveBox,
    @JsonProperty("avg_food") double avgFood,
    @JsonProperty("avg_cafe") double avgCafe,
    @JsonProperty("avg_culture") double avgCulture,
    @JsonProperty("avg_market") double avgMarket,
    @JsonProperty("avg_medical") double avgMedical

){}
