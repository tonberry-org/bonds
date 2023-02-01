.DEFAULT_GOAL : help

.PHONY: help
help:
	@echo "clean - cleans source tree"
	@echo "build - builds wheel file"
	@echo "package - generates zip file"
	@echo "gen - generates response models"
	@echo "deploy - deploys to lambda deploy s3 bucket"

ZIP_FILE = bonds.zip
ZIP_FILE_2 = bonds_coordinator.zip
WHEEL_FILE = realpath ./dist/*.whl

.PHONY: clean
clean:
	rm -rf ./dist/

.PHONY: build
build:
	poetry build --format wheel

.PHONY: package
package: build
	pip install $(WHEEL_FILE) -t dist && \
	rm -f $(WHEEL_FILE) && \
	cd dist && zip $(ZIP_FILE) * -r -x '*.pyc'\
	cp ${ZIP_FILE} ${ZIP_FILE_2}

.PHONY: deploy
deploy: 
	aws s3 cp dist/${ZIP_FILE} s3://tonberry-lambda-bucket/${ZIP_FILE}  &&\
	aws s3 cp dist/${ZIP_FILE} s3://tonberry-lambda-bucket/${ZIP_FILE_2}