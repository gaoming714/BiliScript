# Define tput color variables
green := $(shell tput setaf 2)
yellow := $(shell tput setaf 3)
red := $(shell tput setaf 1)
reset := $(shell tput sgr0)

PREFIX := BiliScript

default: check build package

# Define check step
check:
	@if [ ! -f "tool/runtime/python.exe" ]; then \
		echo -e "❌ ${red}Missing: ${green}tool/runtime/python.exe${reset}"; \
		exit 1; \
	fi
	@if [ ! -f "tool/ffmpeg/ffmpeg.exe" ]; then \
		echo -e "❌ ${red}Missing: ${green}tool/ffmpeg/ffmpeg.exe${reset}"; \
		exit 1; \
	fi
	@echo -e "✅ ${green}All files checked!${reset}"
	@if [ -d "runtime" ]; then \
		echo -e "💊 ${yellow}runtime exists. Run ${red}make clean${reset} first.(rm runtime folder)"; \
		exit 1; \
	fi

# Define the target to generate requirement.txt
requirement:
	uv export -q -o requirement.txt
	@echo -e "📄 ${green}Generated requirement.txt.${reset}"

# Define build target
build:
	@echo -e "👻 ${green}Copy tool/runtime...${reset}"
	@mkdir -p runtime
	@rsync -avq --delete tool/runtime/ ./runtime/
	@echo -e "👻 ${green}Copy tool/ffmpeg files...${reset}"
	@rsync -av tool/ffmpeg/ ./runtime/
	@echo -e "👻 ${green}Copy tool/utility files...${reset}"
	@rsync -av tool/utility/ ./runtime/
	@$(MAKE) pip

# addon
# @cp -r tool/runtime/* ./runtime/
# @cp tool/ffmpeg/* ./runtime/
# @rsync -av --delete tool/runtime/ ./runtime/

# Define the retry installation target for dependencies
pip:
	uv export -q -o tool/requirement.txt
	@echo -e "👻 ${green}Run pip install...${reset}"
	@max_retries=3; \
	count=0; \
	while [ $$count -le $$max_retries ]; do \
		if runtime/python.exe -m pip install --no-warn-script-location -r tool/requirement.txt; then \
			echo -e "✅ ${green}Dependencies installed!${reset}"; \
			rm -f tool/requirement.txt; \
			exit 0; \
		else \
			echo -e "👻 ${yellow}Install failed${reset}, retry $$count times..."; \
			count=$$((count + 1)); \
		fi; \
	done; \
	echo -e "❌ ${red}Install failed!${reset} Network may need a fix."; \
	exit 1

package:
	@{ git ls-files -co --exclude-standard; echo "runtime/"; } > tool/filelist.txt
	@if [ ! -s tool/filelist.txt ]; then \
		echo -e "🛑 ${red}Error: No files to compress!${reset}"; \
		rm -f tool/filelist.txt; \
		exit 1; \
	fi
	@7z a tool/$(PREFIX).$(shell date +"%Y-%m-%dT%H-%M-%S").7z @tool/filelist.txt
	rm -f tool/filelist.txt
	@echo -e "✅ ${green}Compression done!${reset}"

clean:
	@echo -e "👻 ${yellow}Removing the 'runtime' directory...${reset}"
	@rm -rf runtime
	@echo -e "✅ ${green}runtime directory cleaned!${reset}"

