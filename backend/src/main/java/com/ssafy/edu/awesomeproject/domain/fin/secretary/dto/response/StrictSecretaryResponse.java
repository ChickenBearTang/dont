package com.ssafy.edu.awesomeproject.domain.fin.secretary.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StrictSecretaryResponse {
    @JsonProperty("is_approved")
    private boolean approved;

    @JsonProperty("fact_violence_comment")
    private String factViolenceComment;

    @JsonProperty("reasoning")
    private List<String> reasoning;
}
