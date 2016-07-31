VERSION_NUM = $(shell cat VERSION)
IMAGE = luinstra/foaas_slackbot:$(VERSION_NUM)

all: build push

build:
	docker-compose build
	docker tag foaas_slackbot $(IMAGE)

push:
	docker push $(IMAGE)

.PHONY: \
	all \
	build \
	push
