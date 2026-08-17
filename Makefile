IMAGE := personalization-case

.PHONY: build run stop logs

build:
	docker build -t $(IMAGE) .

run:
	docker run --rm -d -p 8000:8000 --env-file .env --name $(IMAGE) $(IMAGE)

stop:
	docker stop $(IMAGE)

logs:
	docker logs -f $(IMAGE)
