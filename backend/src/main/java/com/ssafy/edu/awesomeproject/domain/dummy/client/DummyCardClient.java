package com.ssafy.edu.awesomeproject.domain.dummy.client;

import com.ssafy.edu.awesomeproject.domain.dummy.client.dto.request.DummyCreateCreditCardRequest;
import com.ssafy.edu.awesomeproject.domain.dummy.client.dto.response.DummyCreateCreditCardResponse;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.service.annotation.PostExchange;

public interface DummyCardClient {
    @PostExchange("/ssafy/api/v1/edu/creditCard/createCreditCard")
    DummyCreateCreditCardResponse createCreditCard(@RequestBody DummyCreateCreditCardRequest request);
}
